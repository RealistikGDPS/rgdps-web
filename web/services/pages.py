from dataclasses import dataclass

from poltergeist_core.resources import Snapshot
from poltergeist_core.services import analytics
from poltergeist_core.services import demon_list
from poltergeist_core.services import is_error
from poltergeist_core.services import levels
from poltergeist_core.services import users
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.demon_list import PlayerSummary
from poltergeist_core.services.levels import LevelListing
from poltergeist_core.services.users import PublicProfile
from poltergeist_core.services.users import UserError
from poltergeist_core.utilities import clock

from web.services import series
from web.services.series import Chart

_HOME_LEVELS = 6
_CHART_DAYS = 30


@dataclass(frozen=True, slots=True)
class HomePayload:
    snapshot: Snapshot
    charts: list[Chart]
    featured: LevelListing
    recent: LevelListing


@dataclass(frozen=True, slots=True)
class ProfilePayload:
    profile: PublicProfile
    level_count: int
    demon_list: PlayerSummary


async def home(ctx: AbstractContext) -> HomePayload:
    snapshot = await analytics.snapshot(ctx)
    today = clock.now().date()

    return HomePayload(
        snapshot=snapshot,
        charts=[
            series.chart("New players", snapshot.registrations, _CHART_DAYS, today),
            series.chart("Levels uploaded", snapshot.uploads, _CHART_DAYS, today),
            series.chart("Players seen", snapshot.active_users, _CHART_DAYS, today),
        ],
        featured=await levels.featured(ctx, page=0, size=_HOME_LEVELS),
        recent=await levels.recent(ctx, page=0, size=_HOME_LEVELS),
    )


async def profile(
    ctx: AbstractContext, reference: str
) -> UserError.OnSuccess[ProfilePayload]:
    user = await users.find_by_reference(ctx, reference)

    if user is None:
        return UserError.NOT_FOUND

    public = await users.public_profile(ctx, user.id)

    if is_error(public):
        return public

    return ProfilePayload(
        profile=public,
        level_count=await ctx.levels.count_by_user(user.id),
        demon_list=await demon_list.player_summary(ctx, user_id=user.id),
    )
