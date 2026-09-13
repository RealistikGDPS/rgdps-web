from dataclasses import dataclass
from enum import StrEnum

from gdformat.enums import TimelyType
from poltergeist_core.resources import Level
from poltergeist_core.resources import TimelyLevel
from poltergeist_core.services import administration
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.utilities import clock

from web.services.admin import _common
from web.services.admin._common import BulkOutcome

_QUEUE_SIZE = 20


class Status(StrEnum):
    PAST = "past"
    LIVE = "live"
    QUEUED = "queued"


@dataclass(frozen=True, slots=True)
class Entry:
    timely: TimelyLevel
    level: Level | None
    status: Status


@dataclass(frozen=True, slots=True)
class Queue:
    type: TimelyType
    current: Entry | None
    seconds_left: int
    entries: list[Entry]


def _status(timely: TimelyLevel) -> Status:
    now = clock.now()

    if timely.ends_at <= now:
        return Status.PAST

    if timely.starts_at <= now:
        return Status.LIVE

    return Status.QUEUED


async def _queue(ctx: AbstractContext, timely_type: TimelyType) -> Queue:
    scheduled = await ctx.timely.list_from(timely_type, 0, _QUEUE_SIZE)
    current = await ctx.timely.find_current(timely_type)
    level_ids = [entry.level_id for entry in scheduled]

    if current is not None:
        level_ids.append(current.level_id)

    levels = {level.id: level for level in await ctx.levels.find_many_by_ids(level_ids)}

    return Queue(
        type=timely_type,
        current=None
        if current is None
        else Entry(
            timely=current, level=levels.get(current.level_id), status=Status.LIVE
        ),
        seconds_left=0 if current is None else clock.seconds_until(current.ends_at),
        entries=[
            Entry(timely=entry, level=levels.get(entry.level_id), status=_status(entry))
            for entry in scheduled
        ],
    )


async def queues(ctx: AbstractContext) -> list[Queue]:
    return [await _queue(ctx, timely_type) for timely_type in TimelyType]


async def remove_many(
    ctx: AbstractContext, *, actor_user_id: int, timely_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        timely_ids,
        lambda timely_id: administration.remove_timely(
            ctx, actor_user_id=actor_user_id, timely_id=timely_id
        ),
        verb="Removed",
    )
