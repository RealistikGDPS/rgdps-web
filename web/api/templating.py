import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import jinja2
from gdformat import encoding
from poltergeist_core.resources import LeaderboardKind
from poltergeist_core.resources import UserStats
from poltergeist_core.utilities import clock

from web import settings
from web.api import labels
from web.icons import IconKind
from web.icons import IconRenderer
from web.icons import frames

type IconUrl = Callable[[UserStats, IconKind | None], str]

_STATIC_DIRECTORY = Path(__file__).resolve().parent.parent / "static"
_VERSION_DIGITS = 12


def _static_version() -> str:
    """A digest of the stylesheet and script, so their URLs change with their
    content and no cache in front of the site can serve a stale copy."""

    digest = hashlib.sha256()

    for name in ("css/site.css", "js/site.js"):
        digest.update((_STATIC_DIRECTORY / name).read_bytes())

    return digest.hexdigest()[:_VERSION_DIGITS]


def _number(value: int) -> str:
    return f"{value:,}"


def _age(moment: datetime) -> str:
    return encoding.describe_age(clock.seconds_since(moment))


def _date(moment: datetime) -> str:
    return moment.strftime("%-d %B %Y")


def _icon_id(stats: UserStats, kind: IconKind) -> int:
    match kind:
        case IconKind.CUBE:
            return stats.icon_cube
        case IconKind.SHIP:
            return stats.icon_ship
        case IconKind.BALL:
            return stats.icon_ball
        case IconKind.UFO:
            return stats.icon_ufo
        case IconKind.WAVE:
            return stats.icon_wave
        case IconKind.ROBOT:
            return stats.icon_robot
        case IconKind.SPIDER:
            return stats.icon_spider
        case IconKind.SWING:
            return stats.icon_swing
        case IconKind.JETPACK:
            return stats.icon_jetpack


def _icon_url_builder(renderer: IconRenderer) -> IconUrl:
    def icon_url(stats: UserStats, kind: IconKind | None = None) -> str:
        """The player's chosen form by default. Forms the renderer cannot
        pose show the player's cube instead, so a profile never breaks."""

        resolved = kind or frames.from_icon_type(stats.icon_type)

        if not renderer.supports(resolved):
            resolved = IconKind.CUBE

        glow = 1 if stats.glow else 0

        return (
            f"/icons/{resolved}/{_icon_id(stats, resolved)}/{stats.colour1}/"
            f"{stats.colour2}/{stats.colour3}/{glow}.png"
        )

    return icon_url


_environment = jinja2.Environment(
    loader=jinja2.PackageLoader("web", "templates"),
    autoescape=True,
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
_environment.globals.update(
    site_name=settings.WEB_SITE_NAME,
    download_pc_url=settings.WEB_DOWNLOAD_PC_URL,
    download_android_url=settings.WEB_DOWNLOAD_ANDROID_URL,
    turnstile_site_key=settings.TURNSTILE_SITE_KEY,
    static_version=_static_version(),
    leaderboard_kinds=list(LeaderboardKind),
    icon_kinds=list(IconKind),
)
_environment.filters.update(
    number=_number,
    age=_age,
    date=_date,
    difficulty=labels.difficulty,
    difficulty_class=labels.difficulty_class,
    rating=labels.rating,
    length=labels.length,
    leaderboard_kind=labels.leaderboard_kind,
    mod_level=labels.mod_level,
    icon_kind=labels.icon_kind,
)


def initialise(renderer: IconRenderer) -> None:
    """MUST run before the first render: icon URLs depend on what the renderer
    can draw."""

    _environment.globals["icon_url"] = _icon_url_builder(renderer)


def template(name: str) -> jinja2.Template:
    return _environment.get_template(name)
