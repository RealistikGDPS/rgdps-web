from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.resources import BanType
from poltergeist_core.resources import ModTarget
from poltergeist_core.services import moderation as core_moderation

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import moderation

router = APIRouter(prefix="/moderation")

_BANS = "/admin/moderation/bans"


@router.get("")
async def events(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    actor: str = "",
    target_type: ModTarget | None = None,
    target: str = "",
    page: int = 1,
) -> Response:
    listing = await moderation.events(
        ctx, actor=actor, target_type=target_type, target=target, page=page
    )

    return response.render(
        request, "admin/moderation.html", viewer=operator, listing=listing
    )


@router.get("/bans")
async def bans(
    request: Request, ctx: RequiresContext, operator: RequiresOperator, page: int = 1
) -> Response:
    listing = await moderation.bans(ctx, page=page)

    return response.render(request, "admin/bans.html", viewer=operator, listing=listing)


@router.post("/bans/lift")
async def lift(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await moderation.lift_many(
        ctx, actor_user_id=operator.id, ban_ids=selected
    )

    return response.notice(response.safe_back(request, _BANS), outcome.describe())


@router.post("/bans")
async def ban(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    user_id: Annotated[int, Form()],
    ban_type: Annotated[BanType, Form()],
    days: Annotated[int, Form()] = 7,
    reason: Annotated[str, Form()] = "",
) -> Response:
    response.unwrap(
        request,
        await core_moderation.ban(
            ctx,
            actor_user_id=operator.id,
            target_user_id=user_id,
            ban_type=ban_type,
            days=days or None,
            reason=reason.strip(),
        ),
        viewer=operator,
    )

    return response.notice(_BANS, f"Banned #{user_id}.")
