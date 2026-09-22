from fastapi import APIRouter
from fastapi import Depends

from web.api import dependencies

from . import comments
from . import dashboard
from . import demonlist
from . import flags
from . import levels
from . import moderation
from . import packs
from . import rewards
from . import roles
from . import settings
from . import songs
from . import status
from . import timely
from . import users

_PREFIX = "/admin"


def create_router() -> APIRouter:
    router = APIRouter(prefix=_PREFIX, dependencies=[Depends(dependencies.site)])

    # The dashboard is the prefix itself, which a nested router cannot express.
    router.add_api_route("", dashboard.index, methods=["GET"])
    router.include_router(users.router)
    router.include_router(flags.router)
    router.include_router(levels.router)
    router.include_router(comments.router)
    router.include_router(moderation.router)
    router.include_router(timely.router)
    router.include_router(songs.router)
    router.include_router(rewards.router)
    router.include_router(packs.router)
    router.include_router(demonlist.router)
    router.include_router(roles.router)
    router.include_router(settings.router)
    router.include_router(status.router)

    return router
