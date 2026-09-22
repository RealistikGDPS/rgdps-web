import asyncio
import uuid
from collections.abc import AsyncGenerator
from collections.abc import Awaitable
from collections.abc import Callable
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from poltergeist_core.adapters import boomlings
from poltergeist_core.adapters import mysql
from poltergeist_core.adapters import redis
from poltergeist_core.adapters import storage
from poltergeist_core.services import server_settings
from poltergeist_core.utilities import clock
from poltergeist_core.utilities import logging

from web import settings
from web.adapters import gameserver
from web.adapters import turnstile
from web.icons import IconCache
from web.icons import renderer

from . import account
from . import admin
from . import auth
from . import demonlist
from . import health
from . import icons
from . import pages
from . import response
from . import templating
from . import tools
from .context import HTTPContext
from .interruption import ServiceInterruptionException

logger = logging.get_logger(__name__)

_STATIC_DIRECTORY = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await app.state.mysql.connect()
    logger.info("Connected to the MySQL database.")
    await app.state.redis.initialise()
    logger.info("Connected to the Redis database.")
    # Reading the animation descriptions is file I/O, so it stays off the loop.
    app.state.icons = await asyncio.to_thread(renderer.default)
    templating.initialise(app.state.icons)

    yield

    await app.state.gameserver.close()
    await app.state.captcha.close()
    await app.state.boomlings.close()
    await app.state.redis.aclose()
    await app.state.mysql.disconnect()
    logger.info("Disconnected from the databases.")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=_lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    initialise_mysql(app)
    initialise_redis(app)
    initialise_storage(app)
    initialise_boomlings(app)
    initialise_captcha(app)
    initialise_gameserver(app)
    initialise_icons(app)
    initialise_interruptions(app)
    initialise_request_tracing(app)
    create_routes(app)

    logger.debug("Finalised the app instance.")

    return app


def initialise_mysql(app: FastAPI) -> None:
    app.state.mysql = mysql.default()
    logger.debug("Attached MySQL to the app instance.")


def initialise_redis(app: FastAPI) -> None:
    app.state.redis = redis.default()
    logger.debug("Attached Redis to the app instance.")


def initialise_storage(app: FastAPI) -> None:
    app.state.storage = storage.default()
    logger.debug("Attached object storage to the app instance.")


def initialise_boomlings(app: FastAPI) -> None:
    app.state.boomlings = boomlings.default()
    logger.debug("Attached the Boomlings client to the app instance.")


def initialise_captcha(app: FastAPI) -> None:
    app.state.captcha = turnstile.default()
    logger.debug("Attached the captcha client to the app instance.")


def initialise_gameserver(app: FastAPI) -> None:
    app.state.gameserver = gameserver.default()
    app.state.started_at = clock.now()
    logger.debug("Attached the game server client to the app instance.")


def initialise_icons(app: FastAPI) -> None:
    app.state.icon_cache = IconCache(settings.WEB_ICON_CACHE_SIZE)
    logger.debug("Attached the icon cache to the app instance.")


def initialise_interruptions(app: FastAPI) -> None:
    @app.exception_handler(ServiceInterruptionException)
    async def handle_interruption(
        _: Request, exception: ServiceInterruptionException
    ) -> Response:
        return exception.response

    async def error_page(
        request: Request, status: HTTPStatus, message: str
    ) -> Response:
        # These handlers run before any dependency, so the site settings the
        # chrome needs are loaded here by hand.
        request.state.site = await server_settings.current(HTTPContext(request))

        return response.render(
            request,
            "error.html",
            viewer=None,
            status=status,
            message=message,
            status_code=status,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(
        request: Request, _: RequestValidationError
    ) -> Response:
        if request.method == "POST":
            return await error_page(
                request,
                HTTPStatus.BAD_REQUEST,
                "The form was not filled in correctly.",
            )

        return await error_page(request, HTTPStatus.NOT_FOUND, "There is nothing here.")

    @app.exception_handler(HTTPStatus.NOT_FOUND)
    async def handle_not_found(request: Request, _: Exception) -> Response:
        return await error_page(request, HTTPStatus.NOT_FOUND, "There is nothing here.")

    logger.debug("Initialised the service interruption handler.")


def initialise_request_tracing(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.uuid = str(uuid.uuid4())
        logging.add_context(uuid=request.state.uuid, path=request.url.path)

        try:
            return await call_next(request)
        finally:
            logging.clear_context()

    logger.debug("Initialised request tracing.")


def create_routes(app: FastAPI) -> None:
    app.include_router(pages.router)
    app.include_router(auth.router)
    app.include_router(account.router)
    app.include_router(tools.router)
    app.include_router(demonlist.router)
    app.include_router(admin.create_router())
    app.include_router(icons.router)
    app.include_router(health.router)
    app.mount("/static", StaticFiles(directory=_STATIC_DIRECTORY), name="static")
    logger.debug("Attached routers to the app instance.")
