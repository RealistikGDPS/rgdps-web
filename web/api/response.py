import hmac
import secrets
from collections.abc import Awaitable
from collections.abc import Callable
from enum import StrEnum
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from poltergeist_core.resources import User
from poltergeist_core.services import ServiceError
from poltergeist_core.services import auth
from poltergeist_core.services import is_error
from poltergeist_core.utilities import logging

from web import settings
from web.api import copy
from web.api import templating
from web.api.interruption import ServiceInterruptionException
from web.errors import WebError

logger = logging.get_logger(__name__)

SESSION_COOKIE = "rgdps_session"
CSRF_COOKIE = "rgdps_csrf"
FLASH_COOKIE = "rgdps_flash"
_FLASH_SECONDS = 60
_CSRF_BYTES = 32
_ICON_CACHE_CONTROL = "public, max-age=31536000, immutable"


class Flash(StrEnum):
    """One-shot notices carried across a redirect. The wording lives in the
    base template, so the cookie only ever holds one of these codes."""

    LOGGED_IN = "logged_in"
    LOGGED_OUT = "logged_out"
    REGISTERED = "registered"
    PASSWORD_CHANGED = "password_changed"
    USERNAME_CHANGED = "username_changed"


def _set_cookie(
    response: Response, name: str, value: str, *, max_age: int | None
) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        path="/",
        secure=settings.WEB_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


def csrf_token(request: Request) -> str:
    """The double-submit token: kept in a cookie the browser sends back and
    echoed into every form. A fresh one is minted once per request when the
    cookie is missing and written out with the page."""

    existing = request.cookies.get(CSRF_COOKIE)

    if existing:
        return existing

    minted = getattr(request.state, "csrf_token", None)

    if isinstance(minted, str):
        return minted

    request.state.csrf_token = secrets.token_urlsafe(_CSRF_BYTES)

    return str(request.state.csrf_token)


def verify_csrf(request: Request, presented: str) -> WebError | None:
    expected = request.cookies.get(CSRF_COOKIE)

    if not expected or not hmac.compare_digest(expected, presented):
        return WebError.CSRF_INVALID

    return None


def _pending_flash(request: Request) -> Flash | None:
    raw = request.cookies.get(FLASH_COOKIE)

    if raw is None:
        return None

    try:
        return Flash(raw)
    except ValueError:
        return None


def render(
    request: Request,
    name: str,
    *,
    viewer: User | None,
    status: int = HTTPStatus.OK,
    **context: Any,
) -> Response:
    token = csrf_token(request)
    flash = _pending_flash(request)
    body = templating.template(name).render(
        request=request, viewer=viewer, csrf_token=token, flash=flash, **context
    )
    response = HTMLResponse(body, status_code=status)

    if request.cookies.get(CSRF_COOKIE) != token:
        _set_cookie(response, CSRF_COOKIE, token, max_age=None)

    if flash is not None:
        response.delete_cookie(FLASH_COOKIE, path="/")

    return response


def redirect(url: str, *, flash: Flash | None = None) -> Response:
    response = RedirectResponse(url, status_code=HTTPStatus.SEE_OTHER)

    if flash is not None:
        _set_cookie(response, FLASH_COOKIE, flash.value, max_age=_FLASH_SECONDS)

    return response


def set_session(response: Response, token: str) -> None:
    _set_cookie(response, SESSION_COOKIE, token, max_age=auth.WEB_SESSION_SECONDS)


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def safe_next(request: Request) -> str:
    """Only a path on this site may be returned to after logging in."""

    target = request.query_params.get("next", "")

    if target.startswith("/") and not target.startswith("//"):
        return target

    return "/"


def png(data: bytes) -> Response:
    return Response(
        content=data,
        media_type="image/png",
        headers={"Cache-Control": _ICON_CACHE_CONTROL},
    )


def unwrap[T](
    request: Request, result: ServiceError.OnSuccess[T], *, viewer: User | None = None
) -> T:
    """The only bridge from a service error to a page: the error page is
    rendered with the error's status."""

    if is_error(result):
        logger.info(
            "Request refused.",
            extra={"error": result.resolve_name(), "status_code": result.status_code()},
        )

        raise ServiceInterruptionException(
            render(
                request,
                "error.html",
                viewer=viewer,
                status=result.status_code(),
                message=copy.explain(result),
                status_code=result.status_code(),
            )
        )

    return result


def require_login(request: Request, viewer: User | None) -> User:
    if viewer is None:
        raise ServiceInterruptionException(
            redirect(f"/login?next={quote(request.url.path)}")
        )

    return viewer


async def form_outcome[T](
    request: Request,
    result: ServiceError.OnSuccess[T],
    *,
    template: str,
    viewer: User | None,
    on_success: Callable[[T], Awaitable[Response]],
    **context: Any,
) -> Response:
    """Refusals re-render the form with the reason instead of leaving the page."""

    if is_error(result):
        return render(
            request,
            template,
            viewer=viewer,
            status=HTTPStatus.BAD_REQUEST,
            error=copy.explain(result),
            **context,
        )

    return await on_success(result)
