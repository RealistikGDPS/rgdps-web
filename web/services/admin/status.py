import asyncio
import platform
import time
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from importlib import metadata

from poltergeist_core import settings as core_settings
from poltergeist_core.adapters.boomlings import BoomlingsError
from poltergeist_core.resources import MySQLProbe
from poltergeist_core.resources import RedisProbe
from poltergeist_core.services import health
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.utilities import clock

from web.adapters.gameserver import ImplementsGameServer

_STORAGE_PROBE_KEY = "healthcheck"
_BOOMLINGS_PROBE_SONG = 1


class State(StrEnum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Tile:
    key: str
    label: str
    state: State
    latency_ms: float | None
    facts: list[tuple[str, str]]


@dataclass(frozen=True, slots=True)
class StackStatus:
    tiles: list[Tile]
    checked_at: datetime

    def as_payload(self) -> dict[str, object]:
        return {
            "checked_at": self.checked_at.isoformat(),
            "tiles": [asdict(tile) for tile in self.tiles],
        }


def _mysql_tile(probe: MySQLProbe | None) -> Tile:
    if probe is None:
        return Tile("mysql", "MySQL", State.DOWN, None, [])

    facts = probe.facts

    return Tile(
        "mysql",
        "MySQL",
        State.UP,
        probe.latency_ms,
        [
            ("Version", facts.version),
            ("Uptime", _duration(facts.uptime_seconds)),
            ("Connections", f"{facts.threads_connected} / {facts.max_connections}"),
            ("Running", str(facts.threads_running)),
            ("Queries", f"{facts.questions:,}"),
        ],
    )


def _redis_tile(probe: RedisProbe | None) -> Tile:
    if probe is None:
        return Tile("redis", "Redis", State.DOWN, None, [])

    facts = probe.facts
    lookups = facts.keyspace_hits + facts.keyspace_misses
    hit_rate = "n/a" if lookups == 0 else f"{facts.keyspace_hits / lookups:.0%}"

    return Tile(
        "redis",
        "Redis",
        State.UP,
        probe.latency_ms,
        [
            ("Version", facts.version),
            ("Uptime", _duration(facts.uptime_seconds)),
            ("Memory", facts.used_memory_human),
            ("Keys", f"{facts.keys:,}"),
            ("Clients", str(facts.connected_clients)),
            ("Hit rate", hit_rate),
        ],
    )


def _duration(seconds: int) -> str:
    days, rest = divmod(max(seconds, 0), 86_400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60

    if days:
        return f"{days}d {hours}h"

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


async def _game_tile(gameserver: ImplementsGameServer) -> Tile:
    probe = await gameserver.probe()

    if probe is None:
        return Tile("game", "Game server", State.DOWN, None, [])

    return Tile(
        "game",
        "Game server",
        State.UP if probe.healthy else State.DOWN,
        probe.latency_ms,
        [("Health", str(probe.status_code)), ("Path", core_settings.APP_PUBLIC_URL)],
    )


async def _storage_tile(ctx: AbstractContext) -> Tile:
    started = time.perf_counter()
    await ctx.storage.load(_STORAGE_PROBE_KEY)

    return Tile(
        "storage",
        "Object storage",
        State.UP,
        round((time.perf_counter() - started) * 1000, 1),
        [("Path", core_settings.APP_STORAGE_PATH)],
    )


async def _website_tile(started_at: datetime) -> Tile:
    """The latency shown is the event loop's own lag: how long a yield takes
    to come back, which is what every request here waits on."""

    started = time.perf_counter()
    await asyncio.sleep(0)
    lag = round((time.perf_counter() - started) * 1000, 1)

    return Tile(
        "web",
        "Website",
        State.UP,
        lag,
        [
            ("Uptime", _duration(clock.seconds_since(started_at))),
            ("Python", platform.python_version()),
            ("Core", metadata.version("poltergeist-core")),
        ],
    )


async def stack(
    ctx: AbstractContext, gameserver: ImplementsGameServer, started_at: datetime
) -> StackStatus:
    probes = await health.stack(ctx)

    return StackStatus(
        tiles=[
            await _game_tile(gameserver),
            _mysql_tile(probes.mysql),
            _redis_tile(probes.redis),
            await _storage_tile(ctx),
            await _website_tile(started_at),
        ],
        checked_at=probes.checked_at,
    )


async def boomlings(ctx: AbstractContext) -> Tile:
    """On demand only: the official servers rate limit us harshly."""

    started = time.perf_counter()
    answer = await ctx.boomlings.fetch_song(_BOOMLINGS_PROBE_SONG)
    latency = round((time.perf_counter() - started) * 1000, 1)
    reachable = answer is not BoomlingsError.UNAVAILABLE
    facts = [("URL", core_settings.BOOMLINGS_URL)]

    if core_settings.BOOMLINGS_PROXY_URL:
        facts.append(("Proxy", core_settings.BOOMLINGS_PROXY_URL))

    return Tile(
        "boomlings",
        "Boomlings",
        State.UP if reachable else State.DOWN,
        latency,
        facts,
    )


def configuration() -> list[tuple[str, str]]:
    return [
        ("Public URL", core_settings.APP_PUBLIC_URL),
        ("Server name", core_settings.APP_SERVER_NAME),
        ("Command prefix", core_settings.APP_COMMAND_PREFIX),
        (
            "Minimum client",
            f"game {core_settings.APP_MIN_GAME_VERSION}, "
            f"binary {core_settings.APP_MIN_BINARY_VERSION}",
        ),
        (
            "Chest cooldowns",
            f"small {core_settings.APP_SMALL_CHEST_SECONDS}s, "
            f"large {core_settings.APP_LARGE_CHEST_SECONDS}s",
        ),
        ("Level limit", f"{core_settings.APP_LEVEL_MAX_BYTES:,} bytes"),
        ("Save limit", f"{core_settings.APP_SAVE_MAX_BYTES:,} bytes"),
        ("Session cache", f"{core_settings.APP_SESSION_SECONDS}s"),
        ("Custom content", core_settings.APP_CUSTOM_CONTENT_URL),
    ]
