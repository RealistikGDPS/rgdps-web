from poltergeist_core.resources import ServerSettings
from poltergeist_core.services import ServiceError
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.reuploads import reupload_level as reupload_in_core

from web.adapters.turnstile import ImplementsCaptcha
from web.errors import WebError
from web.services import tools
from web.services.tools import Tool


async def reupload_level(
    ctx: AbstractContext,
    captcha: ImplementsCaptcha,
    site: ServerSettings,
    *,
    actor_user_id: int,
    level_id: int,
    captcha_token: str,
    ip: str,
) -> ServiceError.OnSuccess[int]:
    """A closed door is reported before the captcha, and the captcha before
    anything else, so bots never consume the reupload allowances."""

    closed = tools.require(site, Tool.LEVEL_REUPLOAD)

    if closed is not None:
        return closed

    if not await captcha.verify(captcha_token, ip=ip):
        return WebError.CAPTCHA_FAILED

    return await reupload_in_core(
        ctx, actor_user_id=actor_user_id, official_id=level_id
    )
