from dataclasses import dataclass
from enum import StrEnum

from poltergeist_core.resources import BanType
from poltergeist_core.resources import Device
from poltergeist_core.resources import Role
from poltergeist_core.resources import User
from poltergeist_core.resources import UserBan
from poltergeist_core.resources import UserStats
from poltergeist_core.services import administration
from poltergeist_core.services import moderation
from poltergeist_core.services import roles
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.users import UserError

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome

_DEVICES_SHOWN = 6


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
