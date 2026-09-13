from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from gdformat.enums import TimelyType
from poltergeist_core.services import timely as core_timely

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import timely

router = APIRouter(prefix="/timely")

_INDEX = "/admin/timely"


@router.get("")
async def index(
    request: Request, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    return response.render(
        request, "admin/timely.html", viewer=operator, queues=await timely.queues(ctx)
    )


@router.post("/schedule")
async def schedule(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    timely_type: Annotated[TimelyType, Form()],
    level_id: Annotated[int, Form()],
) -> Response:
    entry = response.unwrap(
        request,
        await core_timely.schedule(
            ctx, actor_user_id=operator.id, timely_type=timely_type, level_id=level_id
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, f"Scheduled as number {entry.sequence}.")


@router.post("/remove")
async def remove(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await timely.remove_many(
        ctx, actor_user_id=operator.id, timely_ids=selected
    )

    return response.notice(_INDEX, outcome.describe())
