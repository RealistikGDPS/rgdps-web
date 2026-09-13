from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import administration

from web.api import response
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresGameServer
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services.admin import status

router = APIRouter(prefix="/status")

_INDEX = "/admin/status"


@router.get("")
async def index(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    gameserver: RequiresGameServer,
) -> Response:
    stack = await status.stack(ctx, gameserver, request.app.state.started_at)

    return response.render(
        request,
        "admin/status.html",
        viewer=operator,
        stack=stack,
        configuration=status.configuration(),
    )


@router.get("/probe.json")
async def probe(
    request: Request,
    ctx: RequiresContext,
    _: RequiresOperator,
    gameserver: RequiresGameServer,
) -> Response:
    stack = await status.stack(ctx, gameserver, request.app.state.started_at)

    return response.json(stack.as_payload())


@router.post("/boomlings")
async def boomlings(
    request: Request, ctx: RequiresContext, operator: RequiresOperator, _: RequiresCsrf
) -> Response:
    tile = await status.boomlings(ctx)

    if tile.latency_ms is None or tile.state is not status.State.UP:
        return response.notice(_INDEX, "Boomlings did not answer.")

    return response.notice(_INDEX, f"Boomlings answered in {tile.latency_ms:.0f} ms.")


@router.post("/rebuild-leaderboards")
async def rebuild(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
) -> Response:
    total = response.unwrap(
        request,
        await administration.rebuild_leaderboards(ctx, actor_user_id=operator.id),
        viewer=operator,
    )

    return response.notice(_INDEX, f"Ranked {total:,} players.")


@router.post("/revoke-sessions")
async def revoke_sessions(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    user_id: Annotated[int, Form()],
) -> Response:
    response.unwrap(
        request,
        await administration.revoke_sessions(
            ctx, actor_user_id=operator.id, user_id=user_id
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, f"Signed out #{user_id} everywhere.")
