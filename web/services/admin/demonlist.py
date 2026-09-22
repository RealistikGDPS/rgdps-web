from dataclasses import dataclass

from poltergeist_core.resources import DemonListPlacement
from poltergeist_core.resources import DemonListRecord
from poltergeist_core.resources import Level
from poltergeist_core.resources import RecordStatus
from poltergeist_core.resources import User
from poltergeist_core.services import demon_list
from poltergeist_core.services import server_settings
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.demon_list import DemonListError

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome


@dataclass(frozen=True, slots=True)
class PlacementRow:
    """`level` is None once the level has been deleted from the server; the
    placement then needs removing by hand."""

    placement: DemonListPlacement
    level: Level | None
    creator: User | None
    added_by: User | None
    points: int
    approved: int
    pending: int


@dataclass(frozen=True, slots=True)
class Placements:
    rows: list[PlacementRow]
    pending: int


@dataclass(frozen=True, slots=True)
class RecordRow:
    record: DemonListRecord
    user: User | None
    placement: DemonListPlacement | None
    level: Level | None
    reviewer: User | None
    points: int
    # The player's standing approved percent on that level, if any.
    previous_best: int | None


@dataclass(frozen=True, slots=True)
class RecordListing:
    rows: list[RecordRow]
    status: RecordStatus | None
    level: str
    user: str
    page: int
    size: int
    total: int


@dataclass(frozen=True, slots=True)
class PlacementPage:
    row: PlacementRow
    records: list[RecordRow]


async def _pending_total(ctx: AbstractContext) -> int:
    return await ctx.demon_list_records.count_page(
        status=RecordStatus.PENDING, placement_id=None, user_id=None
    )


async def _rows(
    ctx: AbstractContext, placements: list[DemonListPlacement]
) -> list[PlacementRow]:
    site = await server_settings.current(ctx)
    levels = {
        level.id: level
        for level in await ctx.levels.find_many_by_ids(
            [placement.level_id for placement in placements]
        )
    }
    user_ids = [placement.added_by_user_id for placement in placements]
    user_ids.extend(level.user_id for level in levels.values())
    users = {user.id: user for user in await ctx.users.find_many_by_ids(user_ids)}
    counts = await ctx.demon_list_records.count_by_status(
        [placement.id for placement in placements]
    )
    rows: list[PlacementRow] = []

    for placement in placements:
        level = levels.get(placement.level_id)
        by_status = counts.get(placement.id, {})

        rows.append(
            PlacementRow(
                placement=placement,
                level=level,
                creator=None if level is None else users.get(level.user_id),
                added_by=users.get(placement.added_by_user_id),
                points=demon_list.placement_points(placement.position, site),
                approved=by_status.get(RecordStatus.APPROVED, 0),
                pending=by_status.get(RecordStatus.PENDING, 0),
            )
        )

    return rows


async def placements(ctx: AbstractContext) -> Placements:
    return Placements(
        rows=await _rows(ctx, await ctx.demon_list_placements.list_all()),
        pending=await _pending_total(ctx),
    )


async def _record_rows(
    ctx: AbstractContext, records: list[DemonListRecord]
) -> list[RecordRow]:
    site = await server_settings.current(ctx)
    placement_ids = list({record.placement_id for record in records})
    placements = {
        placement.id: placement
        for placement in await ctx.demon_list_placements.find_many_by_ids(placement_ids)
    }
    levels = {
        level.id: level
        for level in await ctx.levels.find_many_by_ids(
            [placement.level_id for placement in placements.values()]
        )
    }
    user_ids = [record.user_id for record in records]
    user_ids.extend(
        record.reviewed_by_user_id
        for record in records
        if record.reviewed_by_user_id is not None
    )
    users = {user.id: user for user in await ctx.users.find_many_by_ids(user_ids)}
    best: dict[tuple[int, int], int] = {}

    for approved in await ctx.demon_list_records.list_approved_by_placements(
        placement_ids
    ):
        key = (approved.placement_id, approved.user_id)
        best[key] = max(best.get(key, 0), approved.percent)

    rows: list[RecordRow] = []

    for record in records:
        placement = placements.get(record.placement_id)
        points = 0

        if placement is not None and placement.deleted_at is None:
            points = demon_list.record_points(
                demon_list.placement_points(placement.position, site),
                record.percent,
                placement.requirement,
            )

        previous = best.get((record.placement_id, record.user_id))

        rows.append(
            RecordRow(
                record=record,
                user=users.get(record.user_id),
                placement=placement,
                level=None if placement is None else levels.get(placement.level_id),
                reviewer=None
                if record.reviewed_by_user_id is None
                else users.get(record.reviewed_by_user_id),
                points=points,
                previous_best=None
                if previous is None or record.status is RecordStatus.APPROVED
                else previous,
            )
        )

    return rows


async def placement(
    ctx: AbstractContext, placement_id: int
) -> DemonListError.OnSuccess[PlacementPage]:
    found = await ctx.demon_list_placements.find_by_id(placement_id)

    if found is None:
        return DemonListError.NOT_FOUND

    rows = await _rows(ctx, [found])
    records = await ctx.demon_list_records.list_page(
        status=None, placement_id=found.id, user_id=None, page=0, size=_common.PAGE_SIZE
    )

    return PlacementPage(row=rows[0], records=await _record_rows(ctx, records))


async def records(
    ctx: AbstractContext, *, status: str, level: str, user: str, page: int
) -> RecordListing:
    index = forms.page_index(page)
    status_filter = _common.member(RecordStatus, status)
    user_id = int(user) if user.strip().isdecimal() else None
    placement_id = None

    if level.strip().isdecimal():
        found = await ctx.demon_list_placements.find_by_level(
            int(level), include_removed=True
        )
        # A level that was never listed matches nothing rather than everything.
        placement_id = 0 if found is None else found.id

    found_records = await ctx.demon_list_records.list_page(
        status=status_filter,
        placement_id=placement_id,
        user_id=user_id,
        page=index,
        size=_common.PAGE_SIZE,
    )

    return RecordListing(
        rows=await _record_rows(ctx, found_records),
        status=status_filter,
        level=level.strip(),
        user=user.strip(),
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.demon_list_records.count_page(
            status=status_filter, placement_id=placement_id, user_id=user_id
        ),
    )


async def approve_many(
    ctx: AbstractContext, *, actor_user_id: int, record_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        record_ids,
        lambda record_id: demon_list.approve(
            ctx, actor_user_id=actor_user_id, record_id=record_id
        ),
        verb="Approved",
    )


async def reject_many(
    ctx: AbstractContext, *, actor_user_id: int, record_ids: list[int], note: str
) -> BulkOutcome:
    return await _common.run_bulk(
        record_ids,
        lambda record_id: demon_list.reject(
            ctx, actor_user_id=actor_user_id, record_id=record_id, note=note
        ),
        verb="Rejected",
    )


async def delete_many(
    ctx: AbstractContext, *, actor_user_id: int, record_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        record_ids,
        lambda record_id: demon_list.delete_record(
            ctx, actor_user_id=actor_user_id, record_id=record_id
        ),
        verb="Deleted",
    )
