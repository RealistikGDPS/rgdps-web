from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Request
from fastapi import Response
from fastapi import UploadFile
from poltergeist_core import settings

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
from web.services import song_uploads
from web.services import tools
from web.services.tools import Tool

router = APIRouter(prefix="/tools", dependencies=[Depends(dependencies.site)])

_SONG_UPLOAD = "/tools/song-upload"
_LEVEL_REUPLOAD = "/tools/level-reupload"


@router.get("")
async def index(
    request: Request, viewer: RequiresViewer, site: RequiresSite
) -> Response:
    return response.render(
        request, "tools/index.html", viewer=viewer, cards=tools.cards(site)
    )


@router.get("/song-upload")
async def song_upload(
    request: Request, user: RequiresUser, site: RequiresSite
) -> Response:
    response.unwrap(request, tools.require(site, Tool.SONG_UPLOAD), viewer=user)

    return response.render(
        request,
        "tools/song_upload.html",
        viewer=user,
        song_name="",
        artist="",
        max_bytes=settings.APP_SONG_MAX_BYTES,
    )


@router.post("/song-upload")
async def song_upload_submit(
    request: Request,
    ctx: RequiresTransaction,
    user: RequiresUser,
    captcha: RequiresCaptcha,
    site: RequiresSite,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    artist: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    captcha_token: Annotated[str, Form(alias="cf-turnstile-response")] = "",
) -> Response:
    result = await song_uploads.upload_song(
        ctx,
        captcha,
        site,
        actor_user_id=user.id,
        name=name,
        artist_name=artist,
        file=file,
        captcha_token=captcha_token,
        ip=client_ip(request),
    )

    async def uploaded(song_id: int) -> Response:
        return response.notice(
            _SONG_UPLOAD, f"Uploaded as song {song_id}. Use that id in the editor."
        )

    return await response.form_outcome(
        request,
        result,
        template="tools/song_upload.html",
        viewer=user,
        on_success=uploaded,
        song_name=name,
        artist=artist,
        max_bytes=settings.APP_SONG_MAX_BYTES,
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
