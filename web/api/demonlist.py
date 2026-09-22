from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import demon_list

from web.api import dependencies
from web.api import response
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresTransaction
from web.api.dependencies import RequiresUser
from web.api.dependencies import RequiresViewer
from web.services import demonlist

router = APIRouter(prefix="/demonlist", dependencies=[Depends(dependencies.site)])

_INDEX = "/demonlist"
_STANDINGS_PAGE_SIZE = 50


@router.get("")
async def index(
    request: Request, ctx: RequiresContext, viewer: RequiresViewer
) -> Response:
    listing = await demon_list.overview(ctx)

    return response.render(
        request, "demonlist/index.html", viewer=viewer, listing=listing
    )


@router.get("/standings")
async def standings(
    request: Request, ctx: RequiresContext, viewer: RequiresViewer, page: int = 1
) -> Response:
    board = await demon_list.standings(ctx, page=page - 1, size=_STANDINGS_PAGE_SIZE)

    return response.render(
        request, "demonlist/standings.html", viewer=viewer, board=board
    )


@router.post("/records/{record_id}/withdraw")
async def withdraw(
    request: Request,
    record_id: int,
    ctx: RequiresTransaction,
    user: RequiresUser,
    _: RequiresCsrf,
) -> Response:
    response.unwrap(
        request,
        await demon_list.withdraw(ctx, user_id=user.id, record_id=record_id),
        viewer=user,
    )

    return response.notice(
        response.safe_back(request, _INDEX), "Your submission was withdrawn."
    )


@router.get("/{level_id}")
async def level(
    request: Request, level_id: int, ctx: RequiresContext, viewer: RequiresViewer
) -> Response:
    page = response.unwrap(
        request,
        await demonlist.level_page(
            ctx, level_id, None if viewer is None else viewer.id
        ),
        viewer=viewer,
    )

    return response.render(
        request,
        "demonlist/level.html",
        viewer=viewer,
        page=page,
        percent=100,
        video_url="",
        raw_footage_url="",
        notes="",
    )


@router.post("/{level_id}/records")
async def submit(
    request: Request,
    level_id: int,
    ctx: RequiresTransaction,
    user: RequiresUser,
    _: RequiresCsrf,
    percent: Annotated[int, Form()] = 100,
    video_url: Annotated[str, Form()] = "",
    raw_footage_url: Annotated[str, Form()] = "",
    notes: Annotated[str, Form()] = "",
) -> Response:
    page = response.unwrap(
        request, await demonlist.level_page(ctx, level_id, user.id), viewer=user
    )

    result = await demon_list.submit(
        ctx,
        user_id=user.id,
        placement_id=page.detail.placement.id,
        percent=percent,
        video_url=video_url.strip(),
        raw_footage_url=raw_footage_url.strip(),
        notes=notes.strip(),
    )

    async def submitted(_: int) -> Response:
        return response.notice(
            f"{_INDEX}/{level_id}", "Record submitted. A moderator will review it."
        )

    return await response.form_outcome(
        request,
        result,
        template="demonlist/level.html",
        viewer=user,
        on_success=submitted,
        page=page,
        percent=percent,
        video_url=video_url,
        raw_footage_url=raw_footage_url,
        notes=notes,
    )
