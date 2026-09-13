from dataclasses import dataclass

from poltergeist_core.resources import ModAction
from poltergeist_core.resources import ModTarget
from poltergeist_core.resources import User
from poltergeist_core.resources import UserBan
from poltergeist_core.services import moderation
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.moderation import ModerationError

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome


@dataclass(frozen=True, slots=True)
class EventRow:
    action: ModAction
    actor: User | None


@dataclass(frozen=True, slots=True)
class EventListing:
    rows: list[EventRow]
    actor: str
    target_type: ModTarget | None
    target: str
    page: int
    size: int
    total: int


@dataclass(frozen=True, slots=True)
class BanRow:
    ban: UserBan
    user: User | None
    issuer: User | None


@dataclass(frozen=True, slots=True)
class BanListing:
    rows: list[BanRow]
    page: int
    size: int
    total: int


def _optional_id(text: str) -> int | None:
    return int(text) if text.strip().isdecimal() else None


async def events(
    ctx: AbstractContext,
    *,
    actor: str,
    target_type: ModTarget | None,
    target: str,
    page: int,
) -> EventListing:
    index = forms.page_index(page)
    actor_id = _optional_id(actor)
    target_id = _optional_id(target)

    actions = await ctx.mod_actions.list_recent(
        user_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        page=index,
        size=_common.PAGE_SIZE,
    )
    users = {
        user.id: user
        for user in await ctx.users.find_many_by_ids([a.user_id for a in actions])
    }

    return EventListing(
        rows=[
            EventRow(action=action, actor=users.get(action.user_id))
            for action in actions
        ],
        actor=actor.strip(),
        target_type=target_type,
        target=target.strip(),
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.mod_actions.count_recent(
            user_id=actor_id, target_type=target_type, target_id=target_id
        ),
    )


async def bans(ctx: AbstractContext, *, page: int) -> BanListing:
    index = forms.page_index(page)
    active = await ctx.bans.list_all_active(index, _common.PAGE_SIZE)
    user_ids = [ban.user_id for ban in active] + [
        ban.issued_by_user_id for ban in active if ban.issued_by_user_id is not None
    ]
    users = {user.id: user for user in await ctx.users.find_many_by_ids(user_ids)}

    return BanListing(
        rows=[
            BanRow(
                ban=ban,
                user=users.get(ban.user_id),
                issuer=None
                if ban.issued_by_user_id is None
                else users.get(ban.issued_by_user_id),
            )
            for ban in active
        ],
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.bans.count_all_active(),
    )


async def lift_many(
    ctx: AbstractContext, *, actor_user_id: int, ban_ids: list[int]
) -> BulkOutcome:
    found = {ban.id: ban for ban in await ctx.bans.find_many_by_ids(ban_ids)}

    async def lift(ban_id: int) -> ModerationError.OnSuccess[int]:
        ban = found.get(ban_id)

        if ban is None:
            return ModerationError.NOT_FOUND

        return await moderation.unban(
            ctx,
            actor_user_id=actor_user_id,
            target_user_id=ban.user_id,
            ban_type=ban.type,
        )

    return await _common.run_bulk(ban_ids, lift, verb="Lifted")
