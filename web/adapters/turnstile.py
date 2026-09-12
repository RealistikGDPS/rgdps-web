from abc import ABC
from abc import abstractmethod
from typing import override

import httpx
from poltergeist_core.utilities import logging

logger = logging.get_logger(__name__)

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class ImplementsCaptcha(ABC):
    @abstractmethod
    async def verify(self, token: str, *, ip: str) -> bool: ...

    @abstractmethod
    async def close(self) -> None: ...


class TurnstileClient(ImplementsCaptcha):
    """Cloudflare Turnstile. Any failure to reach Cloudflare counts as a
    failed challenge; the form can simply be retried."""

    __slots__ = ("_client", "_secret")

    def __init__(self, *, secret: str, timeout_seconds: float) -> None:
        self._secret = secret
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    @override
    async def verify(self, token: str, *, ip: str) -> bool:
        if not token:
            return False

        try:
            response = await self._client.post(
                _VERIFY_URL,
                data={"secret": self._secret, "response": token, "remoteip": ip},
            )
        except httpx.HTTPError:
            logger.warning("Turnstile verification could not be reached.")

            return False

        if response.status_code != httpx.codes.OK:
            logger.warning(
                "Turnstile verification refused.",
                extra={"status_code": response.status_code},
            )

            return False

        body = response.json()

        return isinstance(body, dict) and body.get("success") is True

    @override
    async def close(self) -> None:
        await self._client.aclose()


class DisabledCaptcha(ImplementsCaptcha):
    """Every challenge passes; only for development without keys."""

    __slots__ = ()

    @override
    async def verify(self, token: str, *, ip: str) -> bool:
        return True

    @override
    async def close(self) -> None:
        return None


def default() -> ImplementsCaptcha:
    # Local import keeps this module importable without configuration.
    from web import settings

    if not settings.TURNSTILE_SECRET_KEY:
        logger.warning("The captcha is switched off; registration is unprotected.")

        return DisabledCaptcha()

    return TurnstileClient(
        secret=settings.TURNSTILE_SECRET_KEY,
        timeout_seconds=settings.TURNSTILE_TIMEOUT_SECONDS,
    )
