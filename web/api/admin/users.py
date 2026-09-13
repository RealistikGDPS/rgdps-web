from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.resources import BanType
from poltergeist_core.resources import UserKind
from poltergeist_core.services import administration
from poltergeist_core.services import moderation

from web.api import forms
from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import users
from web.services.admin.users import Order

router = APIRouter(prefix="/users")

_INDEX = "/admin/users"


@router.get("")
async def index(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    q: str = "",
    order: Order = Order.NEWEST,
    page: int = 1,
) -> Response:
    listing = await users.listing(ctx, query=q, order=order, page=page)

    return response.render(
        request,
        "admin/users.html",
        viewer=operator,
        listing=listing,
        orders=list(Order),
    )


@router.get("/{user_id}")
async def detail(
    request: Request, user_id: int, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    detail = response.unwrap(request, await users.detail(ctx, user_id), viewer=operator)

    return response.render(request, "admin/user.html", viewer=operator, detail=detail)


@router.post("/ban")
async def ban(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    ban_type: Annotated[BanType, Form()] = BanType.ACCOUNT,
    permanent: Annotated[bool, Form()] = False,
    days: Annotated[int, Form()] = 7,
    reason: Annotated[str, Form()] = "",
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await users.ban_many(
        ctx,
        actor_user_id=operator.id,
        user_ids=selected,
        ban_type=ban_type,
        days=None if permanent else max(days, 1),
        reason=reason.strip(),
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/unban")
async def unban(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    ban_type: Annotated[BanType, Form(alias="unban_type")] = BanType.ACCOUNT,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await users.unban_many(
        ctx, actor_user_id=operator.id, user_ids=selected, ban_type=ban_type
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/roles/assign")
async def assign_role(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    role: Annotated[str, Form()] = "",
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await users.assign_role_many(
        ctx, actor_user_id=operator.id, user_ids=selected, role_name=role
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/roles/revoke")
async def revoke_role(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    role: Annotated[str, Form()] = "",
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await users.revoke_role_many(
        ctx, actor_user_id=operator.id, user_ids=selected, role_name=role
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/revoke-sessions")
async def revoke_sessions(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await users.revoke_sessions_many(
        ctx, actor_user_id=operator.id, user_ids=selected
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/{user_id}/password")
async def set_password(
    request: Request,
    user_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    password: Annotated[str, Form()],
) -> Response:
    response.unwrap(
        request,
        await administration.set_password(
            ctx, actor_user_id=operator.id, user_id=user_id, password=password
        ),
        viewer=operator,
    )

    return response.notice(
        f"{_INDEX}/{user_id}",
        "Password set. The player has been signed out everywhere.",
    )


@router.post("/{user_id}/username")
async def rename(
    request: Request,
    user_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    username: Annotated[str, Form()],
) -> Response:
    response.unwrap(
        request,
        await administration.rename_user(
            ctx, actor_user_id=operator.id, user_id=user_id, username=username
        ),
        viewer=operator,
    )

    return response.notice(f"{_INDEX}/{user_id}", "Username changed.")


@router.post("/{user_id}/colour")
async def set_colour(
    request: Request,
    user_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    colour: Annotated[str, Form()] = "",
    clear: Annotated[bool, Form()] = False,
) -> Response:
    packed = (
        None
        if clear
        else response.unwrap(request, forms.parse_colour(colour), viewer=operator)
    )

    response.unwrap(
        request,
        await administration.set_comment_colour(
            ctx, actor_user_id=operator.id, user_id=user_id, colour=packed
        ),
        viewer=operator,
    )

    return response.notice(f"{_INDEX}/{user_id}", "Comment colour updated.")


@router.post("/{user_id}/kind")
async def set_kind(
    request: Request,
    user_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    kind: Annotated[UserKind, Form()],
) -> Response:
    response.unwrap(
        request,
        await moderation.set_user_kind(
            ctx, actor_user_id=operator.id, target_user_id=user_id, kind=kind
        ),
        viewer=operator,
    )

    return response.notice(f"{_INDEX}/{user_id}", "Account kind updated.")
