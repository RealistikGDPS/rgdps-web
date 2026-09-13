from typing import Annotated

from fastapi import Depends
from fastapi import Form
from fastapi import Request
from poltergeist_core.resources import ServerSettings
from poltergeist_core.services import auth
from poltergeist_core.services import is_error
from poltergeist_core.services import server_settings

from web.adapters.gameserver import ImplementsGameServer
from web.adapters.turnstile import ImplementsCaptcha
from web.api import response
from web.api.context import HTTPContext
from web.api.context import HTTPTransactionContext
from web.api.context import transaction_context
from web.icons import IconCache
from web.icons import IconRenderer
from web.viewer import Viewer

RequiresContext = Annotated[HTTPContext, Depends(HTTPContext)]
# NOTE: Function scope commits the transaction before the response is sent, so
# the next page load always observes what the form was just told succeeded.
RequiresTransaction = Annotated[
    HTTPTransactionContext, Depends(transaction_context, scope="function")
]


async def site(request: Request, ctx: RequiresContext) -> ServerSettings:
    """Loaded once per page and kept on the request so `render` can hand it
    to every template. Declared on every HTML router, never per endpoint."""

    site = await server_settings.current(ctx)
    request.state.site = site

    return site


async def _viewer(request: Request, ctx: RequiresContext) -> Viewer | None:
    token = request.cookies.get(response.SESSION_COOKIE)

    if not token:
        return None

    result = await auth.web_authenticate(ctx, token)

    if is_error(result):
        return None

    return Viewer(user=result, grants=await ctx.permissions.effective(result.id))


def _user(request: Request, viewer: RequiresViewer) -> Viewer:
    return response.require_login(request, viewer)


def _operator(request: Request, viewer: RequiresViewer) -> Viewer:
    return response.require_operator(request, viewer)


def _verify_csrf(request: Request, csrf_token: Annotated[str, Form()] = "") -> None:
    response.unwrap(request, response.verify_csrf(request, csrf_token))


def _captcha(request: Request) -> ImplementsCaptcha:
    captcha: ImplementsCaptcha = request.app.state.captcha

    return captcha


def _gameserver(request: Request) -> ImplementsGameServer:
    gameserver: ImplementsGameServer = request.app.state.gameserver

    return gameserver


def _renderer(request: Request) -> IconRenderer:
    renderer: IconRenderer = request.app.state.icons

    return renderer


def _icon_cache(request: Request) -> IconCache:
    cache: IconCache = request.app.state.icon_cache

    return cache


RequiresSite = Annotated[ServerSettings, Depends(site)]
RequiresViewer = Annotated[Viewer | None, Depends(_viewer)]
RequiresUser = Annotated[Viewer, Depends(_user)]
RequiresOperator = Annotated[Viewer, Depends(_operator)]
RequiresCsrf = Annotated[None, Depends(_verify_csrf)]
RequiresCaptcha = Annotated[ImplementsCaptcha, Depends(_captcha)]
RequiresGameServer = Annotated[ImplementsGameServer, Depends(_gameserver)]
RequiresRenderer = Annotated[IconRenderer, Depends(_renderer)]
RequiresIconCache = Annotated[IconCache, Depends(_icon_cache)]
