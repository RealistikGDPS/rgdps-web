import hmac
import secrets
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Mapping
from enum import StrEnum
from http import HTTPStatus
from typing import Any
from typing import NoReturn
from urllib.parse import quote
from urllib.parse import unquote

from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from poltergeist_core.services import ServiceError
from poltergeist_core.services import auth
from poltergeist_core.services import is_error
from poltergeist_core.utilities import logging

from web import settings
from web.api import copy
from web.api import templating
from web.api.interruption import ServiceInterruptionException
from web.errors import WebError
from web.viewer import Viewer

logger = logging.get_logger(__name__)

SESSION_COOKIE = "rgdps_session"
CSRF_COOKIE = "rgdps_csrf"
FLASH_COOKIE = "rgdps_flash"
FLASH_DETAIL_COOKIE = "rgdps_flash_detail"
_FLASH_SECONDS = 60
_FLASH_DETAIL_CHARS = 300
_CSRF_BYTES = 32
_ICON_CACHE_CONTROL = "public, max-age=31536000, immutable"
_NO_STORE = "no-store"
_SAME_SITE_FETCHES = frozenset({"same-origin", "none"})


class Flash(StrEnum):
    """One-shot notices carried across a redirect. The wording lives in the
    base template, so the cookie only ever holds one of these codes; `ADMIN`
    is the exception and reads its sentence from the detail cookie."""

    LOGGED_IN = "logged_in"
    LOGGED_OUT = "logged_out"
    REGISTERED = "registered"
    PASSWORD_CHANGED = "password_changed"
    USERNAME_CHANGED = "username_changed"
    ADMIN = "admin"


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
    """The token must match and, when the browser says where the request came
    from, it must be this site."""

    fetch_site = request.headers.get("sec-fetch-site")

    if fetch_site is not None and fetch_site not in _SAME_SITE_FETCHES:
        return WebError.CSRF_INVALID

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


def _pending_detail(request: Request) -> str:
    raw = request.cookies.get(FLASH_DETAIL_COOKIE)

    return "" if raw is None else unquote(raw)[:_FLASH_DETAIL_CHARS]


def render(
    request: Request,
    name: str,
    *,
    viewer: Viewer | None,
    status: int = HTTPStatus.OK,
    **context: Any,
) -> Response:
    token = csrf_token(request)
    flash = _pending_flash(request)

    body = templating.template(name).render(
        request=request,
        viewer=viewer,
        site=request.state.site,
        csrf_token=token,
        flash=flash,
        flash_detail=_pending_detail(request),
        **context,
    )
    response = HTMLResponse(body, status_code=status)

    if viewer is not None:
        response.headers["Cache-Control"] = _NO_STORE

    if request.cookies.get(CSRF_COOKIE) != token:
        _set_cookie(response, CSRF_COOKIE, token, max_age=None)

    if flash is not None:
        response.delete_cookie(FLASH_COOKIE, path="/")
        response.delete_cookie(FLASH_DETAIL_COOKIE, path="/")

    return response


def redirect(
    url: str, *, flash: Flash | None = None, detail: str | None = None
) -> Response:
    response = RedirectResponse(url, status_code=HTTPStatus.SEE_OTHER)

    if flash is not None:
        _set_cookie(response, FLASH_COOKIE, flash.value, max_age=_FLASH_SECONDS)

    if detail is not None:
        _set_cookie(
            response,
            FLASH_DETAIL_COOKIE,
            quote(detail[:_FLASH_DETAIL_CHARS]),
            max_age=_FLASH_SECONDS,
        )

    return response


def notice(url: str, text: str) -> Response:
    """An admin outcome sentence shown once on the next page."""

    return redirect(url, flash=Flash.ADMIN, detail=text)


def json(data: Mapping[str, object]) -> Response:
    return JSONResponse(dict(data), headers={"Cache-Control": _NO_STORE})


def set_session(response: Response, token: str) -> None:
    _set_cookie(response, SESSION_COOKIE, token, max_age=auth.WEB_SESSION_SECONDS)


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def _safe_path(target: str) -> str | None:
    if target.startswith("/") and not target.startswith("//"):
        return target

    return None


def safe_next(request: Request) -> str:
    """Only a path on this site may be returned to after logging in."""

    return _safe_path(request.query_params.get("next", "")) or "/"


def safe_back(request: Request, fallback: str) -> str:
    """Where an admin form returns to: the listing it was on, filters and all."""

    return _safe_path(request.query_params.get("next", "")) or fallback


def png(data: bytes) -> Response:
    return Response(
        content=data,
        media_type="image/png",
        headers={"Cache-Control": _ICON_CACHE_CONTROL},
    )


def refuse(
    request: Request, error: ServiceError, *, viewer: Viewer | None = None
) -> NoReturn:
    """The only bridge from a service error to a page: the error page is
    rendered with the error's status."""

    logger.info(
        "Request refused.",
        extra={"error": error.resolve_name(), "status_code": error.status_code()},
    )

    raise ServiceInterruptionException(
        render(
            request,
            "error.html",
            viewer=viewer,
            status=error.status_code(),
            message=copy.explain(error),
            status_code=error.status_code(),
        )
    )


def unwrap[T](
    request: Request, result: ServiceError.OnSuccess[T], *, viewer: Viewer | None = None
) -> T:
    if is_error(result):
        refuse(request, result, viewer=viewer)

    return result


def require_login(request: Request, viewer: Viewer | None) -> Viewer:
    if viewer is None:
        raise ServiceInterruptionException(
            redirect(f"/login?next={quote(request.url.path)}")
        )

    return viewer


def require_operator(request: Request, viewer: Viewer | None) -> Viewer:
    """The admin area is invisible to everyone else: a signed-in player gets
    the same page as for any missing address."""

    user = require_login(request, viewer)

    if user.is_operator:
        return user

    logger.info("Admin area refused.", extra={"user_id": user.id})
    refuse(request, WebError.NOT_FOUND, viewer=user)


async def form_outcome[T](
    request: Request,
    result: ServiceError.OnSuccess[T],
    *,
    template: str,
    viewer: Viewer | None,
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
