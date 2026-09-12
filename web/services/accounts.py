from gdformat.requests import Client
from gdformat.requests import RegisterRequest
from poltergeist_core.services import ServiceError
from poltergeist_core.services import auth
from poltergeist_core.services._common import AbstractContext

from web.adapters.turnstile import ImplementsCaptcha
from web.errors import WebError


async def register(
    ctx: AbstractContext,
    captcha: ImplementsCaptcha,
    *,
    username: str,
    email: str,
    password: str,
    confirmation: str,
    captcha_token: str,
    ip: str,
) -> ServiceError.OnSuccess[int]:
    """The captcha is checked before anything else so bots never consume the
    registration rate limits."""

    if password != confirmation:
        return WebError.PASSWORDS_DIFFER

    if not await captcha.verify(captcha_token, ip=ip):
        return WebError.CAPTCHA_FAILED

    request = RegisterRequest(
        client=Client(), name=username, password=password, email=email
    )

    return await auth.register(ctx, request, ip=ip)


async def change_password(
    ctx: AbstractContext,
    user_id: int,
    *,
    current_password: str,
    new_password: str,
    confirmation: str,
) -> ServiceError.OnSuccess[str]:
    if new_password != confirmation:
        return WebError.PASSWORDS_DIFFER

    return await auth.change_password(ctx, user_id, current_password, new_password)
