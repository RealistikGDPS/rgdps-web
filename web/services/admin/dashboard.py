from dataclasses import dataclass

from gdformat.enums import Difficulty
from gdformat.enums import Length
from poltergeist_core.resources import Dashboard
from poltergeist_core.resources import LabelCount
from poltergeist_core.resources import Trend
from poltergeist_core.services import analytics
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.utilities import clock

from web.api import labels
from web.services import series
from web.services.series import Chart

WINDOWS = (7, 30, 90, 365)
_DEFAULT_WINDOW = 30
_HOURS = 24


@dataclass(frozen=True, slots=True)
class Kpi:
    label: str
    value: int
    delta: int | None = None
    spark: list[int] | None = None
    inverted: bool = False


@dataclass(frozen=True, slots=True)
class Slice:
    label: str
    count: int
    css: str


@dataclass(frozen=True, slots=True)
class Overview:
    dashboard: Dashboard
    kpis: list[Kpi]
    charts: list[Chart]
    difficulties: list[Slice]
    stars: list[Slice]
    lengths: list[Slice]
    hours: list[int]


def window(days: int) -> int:
    return days if days in WINDOWS else _DEFAULT_WINDOW


def _slices(rows: list[LabelCount], kind: str) -> list[Slice]:
    match kind:
        case "difficulty":
            return [
                Slice(
                    label=labels.difficulty(Difficulty(row.label)),
                    count=row.count,
                    css=labels.difficulty_class(Difficulty(row.label)),
                )
                for row in rows
            ]
        case "stars":
            return [
                Slice(
                    label=f"{row.label} star{'s' if row.label != 1 else ''}",
                    count=row.count,
                    css="stars",
                )
                for row in rows
            ]
        case _:
            return [
                Slice(label=labels.length(Length(row.label)), count=row.count, css="")
                for row in rows
            ]


def _hours(rows: list[LabelCount]) -> list[int]:
    counts = {row.label: row.count for row in rows}

    return [counts.get(hour, 0) for hour in range(_HOURS)]


def _chart(title: str, trend: Trend, days: int) -> Chart:
    return series.chart(title, trend.current, days, clock.now().date())


async def overview(ctx: AbstractContext, days: int) -> Overview:
    days = window(days)
    dashboard = await analytics.dashboard(ctx, days=days)
    totals = dashboard.totals

    kpis = [
        Kpi(
            "Players",
            totals.users,
            dashboard.registrations.delta,
            dashboard.registrations.sparkline,
        ),
        Kpi(
            "Seen recently",
            dashboard.active_users.current_total,
            dashboard.active_users.delta,
            dashboard.active_users.sparkline,
        ),
        Kpi(
            "Levels",
            totals.levels,
            dashboard.uploads.delta,
            dashboard.uploads.sparkline,
        ),
        Kpi(
            "Level comments",
            totals.comments,
            dashboard.comments.delta,
            dashboard.comments.sparkline,
        ),
        Kpi(
            "Mod actions",
            dashboard.mod_actions.current_total,
            dashboard.mod_actions.delta,
            dashboard.mod_actions.sparkline,
            inverted=True,
        ),
        Kpi("Rated levels", totals.rated_levels),
        Kpi("Featured levels", totals.featured_levels),
        Kpi("Profile posts", totals.account_comments),
        Kpi("Cloud saves", totals.saves),
        Kpi("Active bans", totals.active_bans, inverted=True),
    ]

    return Overview(
        dashboard=dashboard,
        kpis=kpis,
        charts=[
            _chart("Registrations", dashboard.registrations, days),
            _chart("Players seen", dashboard.active_users, days),
            _chart("Level uploads", dashboard.uploads, days),
            _chart("Comments", dashboard.comments, days),
            _chart("Moderation actions", dashboard.mod_actions, days),
        ],
        difficulties=_slices(dashboard.difficulties, "difficulty"),
        stars=_slices(dashboard.stars, "stars"),
        lengths=_slices(dashboard.lengths, "length"),
        hours=_hours(dashboard.comment_hours),
    )
