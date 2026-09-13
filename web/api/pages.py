from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from poltergeist_core.resources import LeaderboardKind
from poltergeist_core.services import users

from web.api import dependencies
from web.api import response
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresViewer
from web.services import pages

router = APIRouter(dependencies=[Depends(dependencies.site)])

_LEADERBOARD_PAGE_SIZE = 50


@router.get("/")
async def home(
    request: Request, ctx: RequiresContext, viewer: RequiresViewer
) -> Response:
    payload = await pages.home(ctx)

    return response.render(request, "home.html", viewer=viewer, payload=payload)


@router.get("/downloads")
async def downloads(request: Request, viewer: RequiresViewer) -> Response:
    return response.render(request, "downloads.html", viewer=viewer)


@router.get("/leaderboards")
async def leaderboards() -> Response:
    return response.redirect(f"/leaderboards/{LeaderboardKind.STARS}")


@router.get("/leaderboards/{kind}")
async def leaderboard(
    request: Request,
    kind: LeaderboardKind,
    ctx: RequiresContext,
    viewer: RequiresViewer,
    page: int = 1,
) -> Response:
    board = await users.public_leaderboard(
        ctx, kind, page=page - 1, size=_LEADERBOARD_PAGE_SIZE
    )

    return response.render(
        request, "leaderboards.html", viewer=viewer, kind=kind, board=board
    )


@router.get("/users/{reference}")
async def user(
    request: Request, reference: str, ctx: RequiresContext, viewer: RequiresViewer
) -> Response:
    payload = response.unwrap(
        request, await pages.profile(ctx, reference), viewer=viewer
    )

    return response.render(request, "user.html", viewer=viewer, payload=payload)
