from dataclasses import dataclass
from enum import StrEnum

from poltergeist_core.resources import FlagKind
from poltergeist_core.resources import FlagStatus
from poltergeist_core.resources import Level
from poltergeist_core.resources import User
from poltergeist_core.resources import UserFlag
from poltergeist_core.services import flags
from poltergeist_core.services._common import AbstractContext

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome


@dataclass(frozen=True, slots=True)
class FlagRow:
    """`users` covers the flagged account and every account its evidence
    names, so the template can link them all."""

    flag: UserFlag
    user: User | None
    level: Level | None
    users: dict[int, User]
    open_count: int


@dataclass(frozen=True, slots=True)
class FlagListing:
    rows: list[FlagRow]
    status: FlagStatus | None
    kind: FlagKind | None
    user: str
    page: int
    size: int
    total: int


def _member[E: StrEnum](kind: type[E], text: str) -> E | None:
    """A select's "any" option posts an empty value, which no enum holds."""

    return kind(text) if text in kind else None


def _linked_ids(flag: UserFlag) -> list[int]:
    if flag.evidence is None:
        return []

    return [int(entry["user_id"]) for entry in flag.evidence.get("linked", [])]


async def listing(
    ctx: AbstractContext,
    *,
    status: str,
    kind: str,
    user: str,
    page: int,
) -> FlagListing:
    index = forms.page_index(page)
    status_filter = _member(FlagStatus, status)
    kind_filter = _member(FlagKind, kind)
    user_id = int(user) if user.strip().isdecimal() else None

    found = await ctx.flags.list_page(
        status=status_filter,
        kind=kind_filter,
        user_id=user_id,
        page=index,
        size=_common.PAGE_SIZE,
    )
    user_ids = [flag.user_id for flag in found]

    for flag in found:
        user_ids.extend(_linked_ids(flag))

    users = {entry.id: entry for entry in await ctx.users.find_many_by_ids(user_ids)}
    levels = {
        level.id: level
        for level in await ctx.levels.find_many_by_ids(
            [flag.target_id for flag in found if flag.target_id is not None]
        )
    }
    open_counts = await ctx.flags.count_open_by_users([flag.user_id for flag in found])

    return FlagListing(
        rows=[
            FlagRow(
                flag=flag,
                user=users.get(flag.user_id),
                level=None if flag.target_id is None else levels.get(flag.target_id),
                users={
                    linked_id: users[linked_id]
                    for linked_id in _linked_ids(flag)
                    if linked_id in users
                },
                open_count=open_counts.get(flag.user_id, 0),
            )
            for flag in found
        ],
        status=status_filter,
        kind=kind_filter,
        user=user.strip(),
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.flags.count_page(
            status=status_filter, kind=kind_filter, user_id=user_id
        ),
    )


async def dismiss_many(
    ctx: AbstractContext, *, actor_user_id: int, flag_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        flag_ids,
        lambda flag_id: flags.dismiss(
            ctx, actor_user_id=actor_user_id, flag_id=flag_id
        ),
        verb="Dismissed",
    )


async def ban_many(
    ctx: AbstractContext,
    *,
    actor_user_id: int,
    flag_ids: list[int],
    days: int | None,
    reason: str,
) -> BulkOutcome:
    return await _common.run_bulk(
        flag_ids,
        lambda flag_id: flags.ban_from_flag(
            ctx,
            actor_user_id=actor_user_id,
            flag_id=flag_id,
            days=days,
            reason=reason,
        ),
        verb="Banned",
    )


async def restore_many(
    ctx: AbstractContext, *, actor_user_id: int, flag_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        flag_ids,
        lambda flag_id: flags.restore_from_flag(
            ctx, actor_user_id=actor_user_id, flag_id=flag_id
        ),
        verb="Restored",
    )
