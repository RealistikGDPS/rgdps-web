import asyncio

from fastapi import APIRouter
from fastapi import Request
from fastapi import Response

from web.api import response
from web.api.dependencies import RequiresIconCache
from web.api.dependencies import RequiresRenderer
from web.icons import IconKind
from web.icons import IconRequest

router = APIRouter(prefix="/icons")


@router.get("/{kind}/{icon_id}/{colour1}/{colour2}/{colour3}/{glow}.png")
async def icon(
    request: Request,
    kind: IconKind,
    icon_id: int,
    colour1: int,
    colour2: int,
    colour3: int,
    glow: int,
    renderer: RequiresRenderer,
    cache: RequiresIconCache,
) -> Response:
    wanted = IconRequest(
        kind=kind,
        icon_id=icon_id,
        colour1=colour1,
        colour2=colour2,
        colour3=colour3,
        glow=glow == 1,
    )
    cached = cache.get(wanted)

    if cached is not None:
        return response.png(cached)

    data = response.unwrap(request, await asyncio.to_thread(renderer.render, wanted))
    cache.put(wanted, data)

    return response.png(data)
