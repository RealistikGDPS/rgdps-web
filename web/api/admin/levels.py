from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from gdformat.enums import DemonDifficulty
from gdformat.enums import SendFeature
from gdformat.enums import TimelyType
from gdformat.enums import Visibility

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import levels
from web.services.admin.levels import Filters
from web.services.admin.levels import Order
from web.services.admin.levels import Rated

router = APIRouter(prefix="/levels")

_INDEX = "/admin/levels"
_QUEUES = "/admin/levels/queues"


@router.get("")
async def index(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    q: str = "",
    order: Order = Order.RECENT,
    rated: Rated = Rated.ALL,
    creator: str = "",
    page: int = 1,
) -> Response:
    filters = Filters(query=q, order=order, rated=rated, creator=creator, page=page)
    listing = await levels.listing(ctx, filters)

    return response.render(
        request,
        "admin/levels.html",
        viewer=operator,
        listing=listing,
        orders=list(Order),
        rated_options=list(Rated),
    )


@router.get("/queues")
async def queues(
    request: Request, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    return response.render(
        request, "admin/queues.html", viewer=operator, queues=await levels.queues(ctx)
    )


@router.get("/{level_id}")
async def detail(
    request: Request, level_id: int, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    detail = response.unwrap(
        request, await levels.detail(ctx, level_id), viewer=operator
    )

    return response.render(request, "admin/level.html", viewer=operator, detail=detail)


@router.post("/rate")
async def rate(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    stars: Annotated[int, Form()] = 0,
    feature: Annotated[SendFeature | None, Form()] = None,
    demon: Annotated[DemonDifficulty | None, Form()] = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.rate_many(
        ctx,
        actor_user_id=operator.id,
        level_ids=selected,
        stars=stars,
        feature=feature,
        demon=demon,
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/visibility")
async def visibility(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    visibility: Annotated[Visibility, Form()] = Visibility.PUBLIC,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.set_visibility_many(
        ctx, actor_user_id=operator.id, level_ids=selected, visibility=visibility
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/lock")
async def lock(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.set_locked_many(
        ctx, actor_user_id=operator.id, level_ids=selected, locked=True
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/unlock")
async def unlock(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.set_locked_many(
        ctx, actor_user_id=operator.id, level_ids=selected, locked=False
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/timely")
async def schedule(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    timely_type: Annotated[TimelyType, Form()] = TimelyType.DAILY,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.schedule_many(
        ctx, actor_user_id=operator.id, level_ids=selected, timely_type=timely_type
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/delete")
async def delete(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.delete_many(
        ctx, actor_user_id=operator.id, level_ids=selected
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/suggestions/rate")
async def rate_suggested(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.rate_suggested_many(
        ctx, actor_user_id=operator.id, level_ids=selected
    )

    return response.notice(response.safe_back(request, _QUEUES), outcome.describe())


@router.post("/suggestions/dismiss")
async def dismiss(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.dismiss_many(
        ctx, actor_user_id=operator.id, level_ids=selected
    )

    return response.notice(response.safe_back(request, _QUEUES), outcome.describe())


@router.post("/reports/resolve")
async def resolve(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await levels.resolve_many(
        ctx, actor_user_id=operator.id, level_ids=selected
    )

    return response.notice(response.safe_back(request, _QUEUES), outcome.describe())
