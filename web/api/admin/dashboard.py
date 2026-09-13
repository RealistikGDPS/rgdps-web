from fastapi import Request
from fastapi import Response

from web.api import response
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresOperator
from web.services.admin import dashboard


async def index(
    request: Request, ctx: RequiresContext, operator: RequiresOperator, days: int = 30
) -> Response:
    overview = await dashboard.overview(ctx, days)

    return response.render(
        request,
        "admin/dashboard.html",
        viewer=operator,
        overview=overview,
        windows=dashboard.WINDOWS,
    )
