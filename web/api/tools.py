from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import Response

from web.api import dependencies
from web.api import response
from web.api.context import client_ip
from web.api.dependencies import RequiresCaptcha
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresSite
from web.api.dependencies import RequiresTransaction
from web.api.dependencies import RequiresUser
from web.api.dependencies import RequiresViewer
from web.services import reuploads
from web.services import tools
from web.services.tools import Tool

router = APIRouter(prefix="/tools", dependencies=[Depends(dependencies.site)])

_LEVEL_REUPLOAD = "/tools/level-reupload"


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
    request: Request, user: RequiresUser, site: RequiresSite
) -> Response:
    response.unwrap(request, tools.require(site, Tool.LEVEL_REUPLOAD), viewer=user)

    return response.render(
        request, "tools/level_reupload.html", viewer=user, level_id=""
    )


@router.post("/level-reupload")
async def level_reupload_submit(
    request: Request,
    ctx: RequiresTransaction,
    user: RequiresUser,
    captcha: RequiresCaptcha,
    site: RequiresSite,
    _: RequiresCsrf,
    level_id: Annotated[int, Form()],
    captcha_token: Annotated[str, Form(alias="cf-turnstile-response")] = "",
) -> Response:
    result = await reuploads.reupload_level(
        ctx,
        captcha,
        site,
        actor_user_id=user.id,
        level_id=level_id,
        captcha_token=captcha_token,
        ip=client_ip(request),
    )

    async def reuploaded(new_id: int) -> Response:
        return response.notice(
            _LEVEL_REUPLOAD,
            f"Reuploaded as level {new_id}. Search for it by id in the game.",
        )

    return await response.form_outcome(
        request,
        result,
        template="tools/level_reupload.html",
        viewer=user,
        on_success=reuploaded,
        level_id=level_id,
    )
