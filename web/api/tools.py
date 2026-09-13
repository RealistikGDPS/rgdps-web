from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response

from web.api import dependencies
from web.api import response
from web.api.dependencies import RequiresSite
from web.api.dependencies import RequiresViewer
from web.services import tools
from web.services.tools import Tool

router = APIRouter(prefix="/tools", dependencies=[Depends(dependencies.site)])


@router.get("")
async def index(
    request: Request, viewer: RequiresViewer, site: RequiresSite
) -> Response:
    return response.render(
        request, "tools/index.html", viewer=viewer, cards=tools.cards(site)
    )


@router.get("/song-reupload")
async def song_reupload(
    request: Request, viewer: RequiresViewer, site: RequiresSite
) -> Response:
    response.unwrap(request, tools.require(site, Tool.SONG_REUPLOAD), viewer=viewer)

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
async def level_reupload(
    request: Request, viewer: RequiresViewer, site: RequiresSite
) -> Response:
    response.unwrap(request, tools.require(site, Tool.LEVEL_REUPLOAD), viewer=viewer)

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
