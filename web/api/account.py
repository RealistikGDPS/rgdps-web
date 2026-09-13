from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.resources import User
from poltergeist_core.services import auth

from web.api import dependencies
from web.api import response
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresTransaction
from web.api.dependencies import RequiresUser
from web.services import accounts

router = APIRouter(prefix="/account", dependencies=[Depends(dependencies.site)])


@router.get("")
async def account(
    request: Request, ctx: RequiresContext, user: RequiresUser
) -> Response:
    return response.render(
        request,
        "account.html",
        viewer=user,
        next_rename_at=await auth.next_rename_at(ctx, user.id),
        username=user.username,
    )


@router.post("/password")
async def change_password(
    request: Request,
    ctx: RequiresTransaction,
    user: RequiresUser,
    _: RequiresCsrf,
    current_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    confirmation: Annotated[str, Form()],
) -> Response:
    result = await accounts.change_password(
        ctx,
        user.id,
        current_password=current_password,
        new_password=new_password,
        confirmation=confirmation,
    )

    async def changed(token: str) -> Response:
        redirected = response.redirect(
            "/account", flash=response.Flash.PASSWORD_CHANGED
        )
        response.set_session(redirected, token)

        return redirected

    return await response.form_outcome(
        request,
        result,
        template="account.html",
        viewer=user,
        on_success=changed,
        next_rename_at=await auth.next_rename_at(ctx, user.id),
        username=user.username,
    )


@router.post("/username")
async def rename(
    request: Request,
    ctx: RequiresTransaction,
    user: RequiresUser,
    _: RequiresCsrf,
    username: Annotated[str, Form()],
) -> Response:
    result = await auth.rename(ctx, user.id, username)

    async def renamed(_: User) -> Response:
        return response.redirect("/account", flash=response.Flash.USERNAME_CHANGED)

    return await response.form_outcome(
        request,
        result,
        template="account.html",
        viewer=user,
        on_success=renamed,
        next_rename_at=await auth.next_rename_at(ctx, user.id),
        username=username,
    )
