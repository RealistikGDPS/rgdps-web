from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.resources import ServerSettings
from poltergeist_core.services import server_settings

from web.api import response
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction

router = APIRouter(prefix="/settings")

_INDEX = "/admin/settings"


@router.get("")
async def index(request: Request, operator: RequiresOperator) -> Response:
    return response.render(request, "admin/settings.html", viewer=operator)


@router.post("")
async def save(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    registration_enabled: Annotated[bool, Form()] = False,
    level_uploads_enabled: Annotated[bool, Form()] = False,
    song_reupload_enabled: Annotated[bool, Form()] = False,
    level_reupload_enabled: Annotated[bool, Form()] = False,
    reupload_bot_user_id: Annotated[int, Form()] = 0,
    level_reupload_daily_limit: Annotated[int, Form()] = 4,
    download_pc_url: Annotated[str, Form()] = "",
    download_android_url: Annotated[str, Form()] = "",
    download_ios_url: Annotated[str, Form()] = "",
    discord_url: Annotated[str, Form()] = "",
    official_stars: Annotated[int, Form()] = 0,
    official_moons: Annotated[int, Form()] = 0,
    official_demons: Annotated[int, Form()] = 0,
    official_secret_coins: Annotated[int, Form()] = 0,
) -> Response:
    wanted = ServerSettings(
        registration_enabled=registration_enabled,
        level_uploads_enabled=level_uploads_enabled,
        song_reupload_enabled=song_reupload_enabled,
        level_reupload_enabled=level_reupload_enabled,
        reupload_bot_user_id=reupload_bot_user_id,
        level_reupload_daily_limit=level_reupload_daily_limit,
        download_pc_url=download_pc_url.strip(),
        download_android_url=download_android_url.strip(),
        download_ios_url=download_ios_url.strip(),
        discord_url=discord_url.strip(),
        official_stars=official_stars,
        official_moons=official_moons,
        official_demons=official_demons,
        official_secret_coins=official_secret_coins,
    )

    response.unwrap(
        request,
        await server_settings.update(ctx, actor_user_id=operator.id, settings=wanted),
        viewer=operator,
    )

    return response.notice(_INDEX, "Settings saved. They apply within half a minute.")
