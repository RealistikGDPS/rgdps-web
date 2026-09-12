from http import HTTPStatus

from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import health

from web.api import response
from web.api.dependencies import RequiresContext

router = APIRouter()


@router.get("/health")
async def check(request: Request, ctx: RequiresContext) -> Response:
    response.unwrap(request, await health.check(ctx))

    return Response(status_code=HTTPStatus.NO_CONTENT)
