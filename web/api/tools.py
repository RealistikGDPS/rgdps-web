from fastapi import APIRouter
from fastapi import Request
from fastapi import Response

from web.api import response
from web.api.dependencies import RequiresViewer

router = APIRouter(prefix="/tools")


@router.get("")
async def tools(request: Request, viewer: RequiresViewer) -> Response:
    return response.render(request, "tools/index.html", viewer=viewer)


@router.get("/song-reupload")
async def song_reupload(request: Request, viewer: RequiresViewer) -> Response:
    return response.render(
        request,
        "tools/placeholder.html",
        viewer=viewer,
        title="Song reupload",
        blurb=(
            "Bring a song from YouTube or a direct link onto the server so it "
            "can be used in levels."
        ),
    )


@router.get("/level-reupload")
async def level_reupload(request: Request, viewer: RequiresViewer) -> Response:
    return response.render(
        request,
        "tools/placeholder.html",
        viewer=viewer,
        title="Level reupload",
        blurb=(
            "Copy a level from the official servers onto RealistikGDPS under "
            "your account."
        ),
    )
