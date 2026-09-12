from typing import Annotated

from fastapi import Depends
from fastapi import Form
from fastapi import Request
from poltergeist_core.resources import User
from poltergeist_core.services import auth
from poltergeist_core.services import is_error

from web.adapters.turnstile import ImplementsCaptcha
from web.api import response
from web.api.context import HTTPContext
from web.api.context import HTTPTransactionContext
from web.api.context import transaction_context
from web.icons import IconCache
from web.icons import IconRenderer

RequiresContext = Annotated[HTTPContext, Depends(HTTPContext)]
# NOTE: Function scope commits the transaction before the response is sent, so
# the next page load always observes what the form was just told succeeded.
RequiresTransaction = Annotated[
    HTTPTransactionContext, Depends(transaction_context, scope="function")
]


async def _viewer(request: Request, ctx: RequiresContext) -> User | None:
    token = request.cookies.get(response.SESSION_COOKIE)

    if not token:
        return None

    result = await auth.web_authenticate(ctx, token)

    return None if is_error(result) else result


def _user(request: Request, viewer: RequiresViewer) -> User:
    return response.require_login(request, viewer)


def _verify_csrf(request: Request, csrf_token: Annotated[str, Form()] = "") -> None:
    response.unwrap(request, response.verify_csrf(request, csrf_token))


def _captcha(request: Request) -> ImplementsCaptcha:
    captcha: ImplementsCaptcha = request.app.state.captcha

    return captcha


def _renderer(request: Request) -> IconRenderer:
    renderer: IconRenderer = request.app.state.icons

    return renderer


def _icon_cache(request: Request) -> IconCache:
    cache: IconCache = request.app.state.icon_cache

    return cache


RequiresViewer = Annotated[User | None, Depends(_viewer)]
RequiresUser = Annotated[User, Depends(_user)]
RequiresCsrf = Annotated[None, Depends(_verify_csrf)]
RequiresCaptcha = Annotated[ImplementsCaptcha, Depends(_captcha)]
RequiresRenderer = Annotated[IconRenderer, Depends(_renderer)]
RequiresIconCache = Annotated[IconCache, Depends(_icon_cache)]
