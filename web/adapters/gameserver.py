import time
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import override

import httpx
from poltergeist_core.utilities import logging

logger = logging.get_logger(__name__)

_HEALTH_PATH = "/health"


@dataclass(frozen=True, slots=True)
class GameServerProbe:
    latency_ms: float
    status_code: int

    @property
    def healthy(self) -> bool:
        return self.status_code < httpx.codes.BAD_REQUEST


class ImplementsGameServer(ABC):
    @abstractmethod
    async def probe(self) -> GameServerProbe | None: ...

    @abstractmethod
    async def close(self) -> None: ...


class GameServerClient(ImplementsGameServer):
    """Times the game server's internal health route. Unreachable is `None`;
    an answer, healthy or not, carries its status."""

    __slots__ = ("_client",)

    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds)

    @override
    async def probe(self) -> GameServerProbe | None:
        started = time.perf_counter()

        try:
            answer = await self._client.get(_HEALTH_PATH)
        except httpx.HTTPError:
            logger.warning("The game server could not be reached.")

            return None

        return GameServerProbe(
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            status_code=answer.status_code,
        )

    @override
    async def close(self) -> None:
        await self._client.aclose()


def default() -> ImplementsGameServer:
    # Local import keeps this module importable without configuration.
    from web import settings

    return GameServerClient(
        base_url=settings.WEB_GAME_SERVER_URL,
        timeout_seconds=settings.WEB_GAME_SERVER_TIMEOUT_SECONDS,
    )
