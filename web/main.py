import sys

from poltergeist_core.utilities import logging
from poltergeist_core.utilities import loop

from web import api
from web import settings

logging.configure_from_yaml()
loop.install_optimal_loop()

logger = logging.get_logger(__name__)

match settings.APP_COMPONENT:
    case "web":
        asgi_app = api.create_app()
    case _:
        logger.error(
            "Unknown application component.",
            extra={"component": settings.APP_COMPONENT},
        )
        sys.exit(1)
