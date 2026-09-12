from dataclasses import dataclass
from datetime import date
from datetime import timedelta

from poltergeist_core.resources import DailyCount
from poltergeist_core.resources import Snapshot
from poltergeist_core.services import analytics
from poltergeist_core.services import is_error
from poltergeist_core.services import levels
from poltergeist_core.services import users
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.levels import LevelListing
from poltergeist_core.services.users import PublicProfile
from poltergeist_core.services.users import UserError
from poltergeist_core.utilities import clock

_HOME_LEVELS = 6
_CHART_DAYS = 30


@dataclass(frozen=True, slots=True)
class Chart:
    """A day-by-day series with the gaps filled, ready to draw as bars."""

    title: str
    points: list[DailyCount]
    peak: int
    total: int


@dataclass(frozen=True, slots=True)
class HomePayload:
    snapshot: Snapshot
    charts: list[Chart]
    featured: LevelListing
    recent: LevelListing


def _chart(title: str, series: list[DailyCount], today: date) -> Chart:
    counts = {entry.day: entry.count for entry in series}
    points = [
        DailyCount(day=day, count=counts.get(day, 0))
        for day in (
            today - timedelta(days=offset) for offset in range(_CHART_DAYS - 1, -1, -1)
        )
    ]

    return Chart(
        title=title,
        points=points,
        peak=max((point.count for point in points), default=0),
        total=sum(point.count for point in points),
    )


@dataclass(frozen=True, slots=True)
class ProfilePayload:
    profile: PublicProfile
    level_count: int


async def home(ctx: AbstractContext) -> HomePayload:
    snapshot = await analytics.snapshot(ctx)
    today = clock.now().date()

    return HomePayload(
        snapshot=snapshot,
        charts=[
            _chart("New players", snapshot.registrations, today),
            _chart("Levels uploaded", snapshot.uploads, today),
            _chart("Players seen", snapshot.active_users, today),
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
        profile=public, level_count=await ctx.levels.count_by_user(user.id)
    )
