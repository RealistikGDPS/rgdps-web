from poltergeist_core.services import ServiceError
from poltergeist_core.services.auth import AuthError
from poltergeist_core.services.users import UserError

from web.errors import WebError
from web.icons import IconError


def explain(error: ServiceError) -> str:
    """What a person reads when a request is refused."""

    match error:
        case AuthError.INVALID_CREDENTIALS:
            return "That username and password were not accepted."
        case AuthError.ACCOUNT_BANNED | AuthError.BANNED:
            return "This account is banned."
        case AuthError.UNAUTHENTICATED:
            return "You need to log in first."
        case AuthError.TOO_MANY_ATTEMPTS:
            return "Too many attempts. Wait a while and try again."
        case AuthError.NAME_TOO_SHORT:
            return "Usernames need at least 3 characters."
        case AuthError.NAME_INVALID:
            return (
                "Usernames are up to 20 letters, digits, spaces, dashes and "
                "underscores."
            )
        case AuthError.NAME_TAKEN:
            return "That username is already taken."
        case AuthError.PASSWORD_TOO_SHORT:
            return "Passwords need at least 6 characters."
        case AuthError.PASSWORD_INVALID:
            return "Passwords are at most 64 characters."
        case AuthError.EMAIL_INVALID:
            return "That email address does not look right."
        case AuthError.EMAIL_TAKEN:
            return "An account with that email address already exists."
        case AuthError.RENAME_TOO_SOON:
            return "You can only change your username once every 30 days."
        case AuthError.USER_NOT_FOUND | UserError.NOT_FOUND:
            return "That player does not exist."
        case WebError.CSRF_INVALID:
            return "The form expired. Go back, reload the page and try again."
        case WebError.CAPTCHA_FAILED:
            return "The captcha was not completed. Try again."
        case WebError.PASSWORDS_DIFFER:
            return "The passwords do not match."
        case WebError.NOT_FOUND:
            return "There is nothing here."
        case IconError.UNKNOWN_KIND | IconError.UNKNOWN_ICON | IconError.INVALID_COLOUR:
            return "That icon cannot be drawn."
        case _:
            return f"Refused: {error.resolve_name()}"
