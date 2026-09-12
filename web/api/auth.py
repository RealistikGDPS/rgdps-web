from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import auth
from poltergeist_core.services.auth import WebLogin

from web.api import response
from web.api.context import client_ip
from web.api.dependencies import RequiresCaptcha
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresTransaction
from web.api.dependencies import RequiresViewer
from web.services import accounts

router = APIRouter()


@router.get("/login")
async def login(request: Request, viewer: RequiresViewer) -> Response:
    if viewer is not None:
        return response.redirect("/")

    return response.render(
        request,
        "login.html",
        viewer=None,
        username="",
        next=response.safe_next(request),
    )


@router.post("/login")
async def login_submit(
    request: Request,
    ctx: RequiresTransaction,
    _: RequiresCsrf,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Response:
    result = await auth.web_login(ctx, username, password, ip=client_ip(request))
    target = response.safe_next(request)

    async def signed_in(login: WebLogin) -> Response:
        redirected = response.redirect(target, flash=response.Flash.LOGGED_IN)
        response.set_session(redirected, login.token)

        return redirected

    return await response.form_outcome(
        request,
        result,
        template="login.html",
        viewer=None,
        on_success=signed_in,
        username=username,
        next=target,
    )


@router.get("/register")
async def register(request: Request, viewer: RequiresViewer) -> Response:
    if viewer is not None:
        return response.redirect("/")

    return response.render(request, "register.html", viewer=None, username="", email="")


@router.post("/register")
async def register_submit(
    request: Request,
    ctx: RequiresTransaction,
    captcha: RequiresCaptcha,
    _: RequiresCsrf,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    confirmation: Annotated[str, Form()],
    captcha_token: Annotated[str, Form(alias="cf-turnstile-response")] = "",
) -> Response:
    ip = client_ip(request)
    result = await accounts.register(
        ctx,
        captcha,
        username=username,
        email=email,
        password=password,
        confirmation=confirmation,
        captcha_token=captcha_token,
        ip=ip,
    )

    async def registered(user_id: int) -> Response:
        login = await auth.web_login(ctx, username, password, ip=ip)
        redirected = response.redirect("/", flash=response.Flash.REGISTERED)

        if isinstance(login, WebLogin):
            response.set_session(redirected, login.token)

        return redirected

    return await response.form_outcome(
        request,
        result,
        template="register.html",
        viewer=None,
        on_success=registered,
        username=username,
        email=email,
    )


@router.post("/logout")
async def logout(request: Request, ctx: RequiresContext, _: RequiresCsrf) -> Response:
    token = request.cookies.get(response.SESSION_COOKIE)

    if token:
        await auth.web_logout(ctx, token)

    redirected = response.redirect("/", flash=response.Flash.LOGGED_OUT)
    response.clear_session(redirected)

    return redirected
