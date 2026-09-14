from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import flags

router = APIRouter(prefix="/flags")

_INDEX = "/admin/flags"


@router.get("")
async def index(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    status: str = "open",
    kind: str = "",
    user: str = "",
    page: int = 1,
) -> Response:
    listing = await flags.listing(ctx, status=status, kind=kind, user=user, page=page)

    return response.render(
        request, "admin/flags.html", viewer=operator, listing=listing
    )


@router.post("/dismiss")
async def dismiss(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await flags.dismiss_many(
        ctx, actor_user_id=operator.id, flag_ids=selected
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/ban")
async def ban(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    permanent: Annotated[bool, Form()] = False,
    days: Annotated[int, Form()] = 30,
    reason: Annotated[str, Form()] = "",
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await flags.ban_many(
        ctx,
        actor_user_id=operator.id,
        flag_ids=selected,
        days=None if permanent else max(days, 1),
        reason=reason.strip(),
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/restore")
async def restore(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await flags.restore_many(
        ctx, actor_user_id=operator.id, flag_ids=selected
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())
