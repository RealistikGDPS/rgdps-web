from enum import StrEnum
from http import HTTPStatus

from poltergeist_core.services import ServiceError


class WebError(ServiceError, StrEnum):
    """Failures that belong to the site itself rather than to the game."""

    CSRF_INVALID = "csrf_invalid"
    CAPTCHA_FAILED = "captcha_failed"
    PASSWORDS_DIFFER = "passwords_differ"
    NOT_FOUND = "not_found"

    def service(self) -> str:
        return "web"

    def status_code(self) -> int:
        match self:
            case WebError.CSRF_INVALID:
                return HTTPStatus.FORBIDDEN
            case WebError.CAPTCHA_FAILED | WebError.PASSWORDS_DIFFER:
                return HTTPStatus.BAD_REQUEST
            case WebError.NOT_FOUND:
                return HTTPStatus.NOT_FOUND
