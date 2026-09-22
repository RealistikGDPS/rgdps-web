import hashlib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import jinja2
from fastapi import Request
from gdformat import encoding
from gdformat.enums import ChestType
from gdformat.enums import DemonDifficulty
from gdformat.enums import MapPackDifficulty
from gdformat.enums import QuestItem
from gdformat.enums import RewardItem
from gdformat.enums import SendFeature
from gdformat.enums import TimelyType
from gdformat.enums import Visibility
from poltergeist_core.resources import BanType
from poltergeist_core.resources import FlagKind
from poltergeist_core.resources import FlagStatus
from poltergeist_core.resources import LeaderboardKind
from poltergeist_core.resources import ModTarget
from poltergeist_core.resources import Permission
from poltergeist_core.resources import RecordStatus
from poltergeist_core.resources import UserKind
from poltergeist_core.resources import UserStats
from poltergeist_core.utilities import clock

from web import settings
from web.api import charts
from web.api import labels
from web.icons import IconKind
from web.icons import IconRenderer
from web.icons import frames

type IconUrl = Callable[[UserStats, IconKind | None], str]

_STATIC_DIRECTORY = Path(__file__).resolve().parent.parent / "static"
_STATIC_FILES = ("css/site.css", "css/admin.css", "js/site.js", "js/admin.js")
_VERSION_DIGITS = 12
_GAUNTLET_ID_MAX = 60
# The vault items an operator may put in a code, in the order they are offered.
_REWARD_ITEMS = (
    RewardItem.ORBS,
    RewardItem.DIAMONDS,
    RewardItem.FIRE_SHARD,
    RewardItem.ICE_SHARD,
    RewardItem.POISON_SHARD,
    RewardItem.SHADOW_SHARD,
    RewardItem.LAVA_SHARD,
    RewardItem.EARTH_SHARD,
    RewardItem.BLOOD_SHARD,
    RewardItem.METAL_SHARD,
    RewardItem.LIGHT_SHARD,
    RewardItem.SOUL_SHARD,
    RewardItem.DEMON_KEY,
    RewardItem.GOLD_KEY,
)


def _static_version() -> str:
    """A digest of the stylesheets and scripts, so their URLs change with
    their content and no cache in front of the site can serve a stale copy."""

    digest = hashlib.sha256()

    for name in _STATIC_FILES:
        digest.update((_STATIC_DIRECTORY / name).read_bytes())

    return digest.hexdigest()[:_VERSION_DIGITS]


def _page_url(request: Request, page: int) -> str:
    """The current listing, filters and all, on another page."""

    url = request.url.include_query_params(page=page)

    return f"{url.path}?{url.query}"


def _back_query(request: Request) -> str:
    """Appended to an admin form's action so it returns to this very listing."""

    url = request.url
    here = f"{url.path}?{url.query}" if url.query else url.path

    return f"?next={quote(here, safe='')}"


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M")


def _ago(moment: datetime | None) -> str:
    if moment is None:
        return "never"

    return f"{encoding.describe_age(clock.seconds_since(moment))} ago"


def _megabytes(size_bytes: int) -> str:
    return f"{size_bytes / 1_048_576:.2f} MB"


def _hex_colour(packed: int | None) -> str:
    return "#ffffff" if packed is None else f"#{packed:06x}"


def _duration(seconds: int) -> str:
    days, rest = divmod(max(seconds, 0), 86_400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60

    if days:
        return f"{days}d {hours}h"

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


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
    turnstile_site_key=settings.TURNSTILE_SITE_KEY,
    status_poll_seconds=settings.WEB_STATUS_POLL_SECONDS,
    static_version=_static_version(),
    page_url=_page_url,
    back_query=_back_query,
    permission=Permission,
    permissions=list(Permission),
    leaderboard_kinds=list(LeaderboardKind),
    icon_kinds=list(IconKind),
    ban_types=list(BanType),
    user_kinds=list(UserKind),
    visibilities=list(Visibility),
    timely_types=list(TimelyType),
    mod_targets=list(ModTarget),
    flag_kinds=list(FlagKind),
    flag_statuses=list(FlagStatus),
    record_statuses=list(RecordStatus),
    quest_items=list(QuestItem),
    chest_types=[ChestType.SMALL, ChestType.LARGE],
    reward_items=list(_REWARD_ITEMS),
    map_pack_difficulties=list(MapPackDifficulty),
    send_features=list(SendFeature),
    demon_difficulties=list(DemonDifficulty),
    gauntlet_ids=list(range(1, _GAUNTLET_ID_MAX + 1)),
)
_environment.filters.update(
    number=_number,
    age=_age,
    ago=_ago,
    date=_date,
    stamp=_stamp,
    megabytes=_megabytes,
    hex_colour=_hex_colour,
    duration=_duration,
    spark_points=charts.spark_points,
    line_path=charts.line_path,
    area_path=charts.area_path,
    difficulty=labels.difficulty,
    difficulty_class=labels.difficulty_class,
    rating=labels.rating,
    level_length=labels.length,
    leaderboard_kind=labels.leaderboard_kind,
    mod_level=labels.mod_level,
    icon_kind=labels.icon_kind,
    ban_type=labels.ban_type,
    user_kind=labels.user_kind,
    visibility=labels.visibility,
    timely_type=labels.timely_type,
    mod_target=labels.mod_target,
    quest_item=labels.quest_item,
    chest_type=labels.chest_type,
    reward_item=labels.reward_item,
    map_pack_difficulty=labels.map_pack_difficulty,
    send_feature=labels.send_feature,
    demon_difficulty=labels.demon_difficulty,
    platform=labels.platform,
    flag_kind=labels.flag_kind,
    flag_status=labels.flag_status,
    record_status=labels.record_status,
    login_source=labels.login_source,
    stats_source=labels.stats_source,
    song_source=labels.song_source,
    gauntlet=labels.gauntlet,
)


def initialise(renderer: IconRenderer) -> None:
    """MUST run before the first render: icon URLs depend on what the renderer
    can draw."""

    _environment.globals["icon_url"] = _icon_url_builder(renderer)


def template(name: str) -> jinja2.Template:
    return _environment.get_template(name)
