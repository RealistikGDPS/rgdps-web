from fastapi import UploadFile
from poltergeist_core import settings
from poltergeist_core.resources import ServerSettings
from poltergeist_core.services import ServiceError
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.song_uploads import upload_song as upload_in_core

from web.adapters.turnstile import ImplementsCaptcha
from web.errors import WebError
from web.services import tools
from web.services.tools import Tool


async def upload_song(
    ctx: AbstractContext,
    captcha: ImplementsCaptcha,
    site: ServerSettings,
    *,
    actor_user_id: int,
    name: str,
    artist_name: str,
    file: UploadFile,
    captcha_token: str,
    ip: str,
) -> ServiceError.OnSuccess[int]:
    """A closed door is reported before the captcha, and the captcha before
    the file is read, so bots never cost memory or allowances."""

    closed = tools.require(site, Tool.SONG_UPLOAD)

    if closed is not None:
        return closed

    if not await captcha.verify(captcha_token, ip=ip):
        return WebError.CAPTCHA_FAILED

    # One byte past the cap is enough for the service to refuse the file.
    data = await file.read(settings.APP_SONG_MAX_BYTES + 1)

    return await upload_in_core(
        ctx, actor_user_id=actor_user_id, name=name, artist_name=artist_name, data=data
    )
