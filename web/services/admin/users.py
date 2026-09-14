from dataclasses import dataclass
from enum import StrEnum

from poltergeist_core.resources import BanType
from poltergeist_core.resources import Device
from poltergeist_core.resources import Role
from poltergeist_core.resources import StatsHistoryEntry
from poltergeist_core.resources import User
from poltergeist_core.resources import UserBan
from poltergeist_core.resources import UserLogin
from poltergeist_core.resources import UserStats
from poltergeist_core.services import administration
from poltergeist_core.services import anticheat
from poltergeist_core.services import flags
from poltergeist_core.services import moderation
from poltergeist_core.services import roles
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.anticheat import LinkedAccount
from poltergeist_core.services.flags import FlagError
from poltergeist_core.services.users import UserError

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome

_DEVICES_SHOWN = 6
_COUNTERS = ("stars", "moons", "demons", "diamonds", "secret_coins", "user_coins")


class Order(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"
    RECENTLY_SEEN = "recently_seen"
    NAME = "name"


@dataclass(frozen=True, slots=True)
class UserRow:
    user: User
    stats: UserStats | None
    roles: list[Role]
    bans: list[UserBan]


@dataclass(frozen=True, slots=True)
class UserListing:
    rows: list[UserRow]
    query: str
    order: Order
    page: int
    size: int
    total: int
    all_roles: list[Role]


@dataclass(frozen=True, slots=True)
class UserDetail:
    user: User
    stats: UserStats | None
    has_password: bool
    roles: list[Role]
    bans: list[UserBan]
    devices: list[Device]
    level_count: int
    all_roles: list[Role]
    open_flags: int
    linked: list[LinkedAccount]


@dataclass(frozen=True, slots=True)
class HistoryRow:
    """`deltas` are against the entry before this one, by counter name."""

    entry: StatsHistoryEntry
    deltas: dict[str, int]


@dataclass(frozen=True, slots=True)
class UserHistory:
    user: User
    rows: list[HistoryRow]
    page: int
    size: int
    total: int


@dataclass(frozen=True, slots=True)
class UserLogins:
    user: User
    rows: list[UserLogin]
    page: int
    size: int
    total: int


async def listing(
    ctx: AbstractContext, *, query: str, order: Order, page: int
) -> UserListing:
    query = query.strip()
    index = forms.page_index(page)

    found = await ctx.users.list_page(
        query=query, order=order.value, page=index, size=_common.PAGE_SIZE
    )
    stats = {
        entry.user_id: entry
        for entry in await ctx.stats.find_many_by_user_ids([u.id for u in found])
    }
    rows = [
        UserRow(
            user=user,
            stats=stats.get(user.id),
            roles=await ctx.roles.list_by_user(user.id),
            bans=await ctx.bans.list_active(user.id),
        )
        for user in found
    ]

    return UserListing(
        rows=rows,
        query=query,
        order=order,
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.users.count_page(query=query),
        all_roles=await ctx.roles.list_all(),
    )


async def detail(ctx: AbstractContext, user_id: int) -> UserError.OnSuccess[UserDetail]:
    user = await ctx.users.find_by_id(user_id)

    if user is None:
        return UserError.NOT_FOUND

    credential = await ctx.credentials.find_by_user_id(user_id)

    return UserDetail(
        user=user,
        stats=await ctx.stats.find_by_user_id(user_id),
        has_password=credential is not None and credential.gjp2_bcrypt is not None,
        roles=await ctx.roles.list_by_user(user_id),
        bans=await ctx.bans.list_active(user_id),
        devices=(await ctx.devices.list_by_user(user_id))[:_DEVICES_SHOWN],
        level_count=await ctx.levels.count_by_user(user_id),
        all_roles=await ctx.roles.list_all(),
        open_flags=await ctx.flags.count_open_by_user(user_id),
        linked=await anticheat.linked_accounts(ctx, user_id),
    )


def _deltas(
    entry: StatsHistoryEntry, previous: StatsHistoryEntry | None
) -> dict[str, int]:
    if previous is None:
        return {}

    return {name: getattr(entry, name) - getattr(previous, name) for name in _COUNTERS}


async def history(
    ctx: AbstractContext, user_id: int, *, page: int
) -> UserError.OnSuccess[UserHistory]:
    user = await ctx.users.find_by_id(user_id)

    if user is None:
        return UserError.NOT_FOUND

    index = forms.page_index(page)
    entries = await ctx.stats_history.list_by_user(user_id, index, _common.PAGE_SIZE)
    # The last row on the page diffs against the first row of the next one.
    beyond = (
        None
        if not entries
        else await ctx.stats_history.find_before(user_id, entries[-1].id)
    )
    previous: list[StatsHistoryEntry | None] = [*entries[1:], beyond]

    return UserHistory(
        user=user,
        rows=[
            HistoryRow(entry=entry, deltas=_deltas(entry, older))
            for entry, older in zip(entries, previous, strict=True)
        ],
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.stats_history.count_by_user(user_id),
    )


async def logins(
    ctx: AbstractContext, user_id: int, *, page: int
) -> UserError.OnSuccess[UserLogins]:
    user = await ctx.users.find_by_id(user_id)

    if user is None:
        return UserError.NOT_FOUND

    index = forms.page_index(page)

    return UserLogins(
        user=user,
        rows=await ctx.logins.list_by_user(user_id, index, _common.PAGE_SIZE),
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.logins.count_by_user(user_id),
    )


async def restore(
    ctx: AbstractContext, *, actor_user_id: int, user_id: int, history_id: int
) -> FlagError.OnSuccess[None]:
    return await flags.restore_stats(
        ctx, actor_user_id=actor_user_id, user_id=user_id, history_id=history_id
    )


async def ban_many(
    ctx: AbstractContext,
    *,
    actor_user_id: int,
    user_ids: list[int],
    ban_type: BanType,
    days: int | None,
    reason: str,
) -> BulkOutcome:
    return await _common.run_bulk(
        user_ids,
        lambda user_id: moderation.ban(
            ctx,
            actor_user_id=actor_user_id,
            target_user_id=user_id,
            ban_type=ban_type,
            days=days,
            reason=reason,
        ),
        verb="Banned",
    )


async def unban_many(
    ctx: AbstractContext, *, actor_user_id: int, user_ids: list[int], ban_type: BanType
) -> BulkOutcome:
    return await _common.run_bulk(
        user_ids,
        lambda user_id: moderation.unban(
            ctx, actor_user_id=actor_user_id, target_user_id=user_id, ban_type=ban_type
        ),
        verb="Lifted",
    )


async def assign_role_many(
    ctx: AbstractContext, *, actor_user_id: int, user_ids: list[int], role_name: str
) -> BulkOutcome:
    return await _common.run_bulk(
        user_ids,
        lambda user_id: roles.assign(
            ctx,
            actor_user_id=actor_user_id,
            target_user_id=user_id,
            role_name=role_name,
            expires_at=None,
        ),
        verb="Assigned",
    )


async def revoke_role_many(
    ctx: AbstractContext, *, actor_user_id: int, user_ids: list[int], role_name: str
) -> BulkOutcome:
    return await _common.run_bulk(
        user_ids,
        lambda user_id: roles.revoke(
            ctx,
            actor_user_id=actor_user_id,
            target_user_id=user_id,
            role_name=role_name,
        ),
        verb="Revoked",
    )


async def revoke_sessions_many(
    ctx: AbstractContext, *, actor_user_id: int, user_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        user_ids,
        lambda user_id: administration.revoke_sessions(
            ctx, actor_user_id=actor_user_id, user_id=user_id
        ),
        verb="Signed out",
    )
