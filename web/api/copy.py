from poltergeist_core.services import ServiceError
from poltergeist_core.services.administration import AdministrationError
from poltergeist_core.services.auth import AuthError
from poltergeist_core.services.comments import CommentError
from poltergeist_core.services.demon_list import DemonListError
from poltergeist_core.services.levels import LevelError
from poltergeist_core.services.moderation import ModerationError
from poltergeist_core.services.packs import PackError
from poltergeist_core.services.reuploads import ReuploadError
from poltergeist_core.services.roles import RoleError
from poltergeist_core.services.server_settings import ServerSettingsError
from poltergeist_core.services.songs import SongError
from poltergeist_core.services.timely import TimelyError
from poltergeist_core.services.users import UserError

from web.errors import WebError
from web.icons import IconError


def _explain_demon_list(error: DemonListError) -> str:
    match error:
        case DemonListError.NOT_PERMITTED:
            return "You are not allowed to do that."
        case DemonListError.LEVEL_NOT_FOUND:
            return "That level does not exist."
        case DemonListError.NOT_FOUND:
            return "That level is not on the demon list."
        case DemonListError.USER_NOT_FOUND:
            return "That player does not exist."
        case DemonListError.ALREADY_LISTED:
            return "That level is already on the list."
        case DemonListError.INVALID_POSITION:
            return "Positions run from 1 to one past the bottom of the list."
        case DemonListError.INVALID_REQUIREMENT:
            return "The requirement is a percent from 1 to 100."
        case DemonListError.INVALID_PERCENT:
            return "The percent runs from 1 to 100."
        case DemonListError.BELOW_REQUIREMENT:
            return "That percent is below this level's list requirement."
        case DemonListError.INVALID_URL:
            return "Links must start with https:// and be at most 255 characters."
        case DemonListError.INVALID_NOTES:
            return "The notes are too long."
        case DemonListError.SUBMISSIONS_CLOSED:
            return "Record submissions are closed at the moment."
        case DemonListError.BANNED:
            return "This account cannot submit demon list records."
        case DemonListError.ALREADY_PENDING:
            return "You already have a record on this level waiting for review."
        case DemonListError.NOT_IMPROVED:
            return "Your approved record on this level is already that good."
        case DemonListError.ALREADY_REVIEWED:
            return "That record has already been reviewed."
        case DemonListError.RATE_LIMITED:
            return "You have used today's record submissions. Try again tomorrow."


def explain(error: ServiceError) -> str:
    """What a person reads when a request is refused."""

    # NOTE: Members of different error enums with the same value compare
    # equal, so an enum whose values overlap the others is told apart by
    # class before the value match below.
    if isinstance(error, DemonListError):
        return _explain_demon_list(error)

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
            return "Passwords are between 6 and 64 characters."
        case AuthError.EMAIL_INVALID:
            return "That email address does not look right."
        case AuthError.EMAIL_TAKEN:
            return "An account with that email address already exists."
        case AuthError.RENAME_TOO_SOON:
            return "You can only change your username once every 30 days."
        case AuthError.REGISTRATION_DISABLED:
            return "Registration is closed at the moment."
        case AuthError.USER_NOT_FOUND | UserError.NOT_FOUND | RoleError.USER_NOT_FOUND:
            return "That player does not exist."
        case (
            AdministrationError.NOT_PERMITTED
            | ModerationError.NOT_PERMITTED
            | ModerationError.NOT_MODERATOR
            | RoleError.NOT_PERMITTED
            | TimelyError.NOT_PERMITTED
            | PackError.NOT_PERMITTED
            | LevelError.NOT_PERMITTED
            | ReuploadError.NOT_PERMITTED
            | CommentError.NOT_PERMITTED
            | SongError.NOT_ALLOWED
            | ServerSettingsError.NOT_PERMITTED
        ):
            return "You are not allowed to do that."
        case ModerationError.TARGET_PROTECTED:
            return "That account is not below yours, so you cannot act on it."
        case RoleError.ROLE_TOO_HIGH:
            return "That role is not below your own, so you cannot hand it out."
        case RoleError.NOT_FOUND:
            return "That role does not exist."
        case LevelError.NOT_FOUND | TimelyError.LEVEL_NOT_FOUND:
            return "That level does not exist."
        case LevelError.LOCKED:
            return "That level is locked."
        case LevelError.UPLOADS_DISABLED:
            return "Level uploads are switched off at the moment."
        case SongError.NOT_FOUND:
            return "That song does not exist."
        case CommentError.NOT_FOUND:
            return "That comment does not exist."
        case (
            AdministrationError.NOT_FOUND
            | ModerationError.NOT_FOUND
            | TimelyError.NOT_FOUND
            | PackError.NOT_FOUND
        ):
            return "That no longer exists."
        case AdministrationError.TAKEN:
            return "That name is already taken."
        case PackError.INVALID:
            return "Every level id must exist, and a gauntlet needs exactly five."
        case ServerSettingsError.INVALID:
            return (
                "Those settings were not accepted: download links must be HTTPS "
                "or a path on this site, the reupload bot must be an existing "
                "user, the daily reupload and demon list allowances at least 1, "
                "the top list points at least 1 and the decay between 1 and 100."
            )
        case ReuploadError.DISABLED:
            return "Level reuploads are switched off at the moment."
        case ReuploadError.BOT_UNAVAILABLE:
            return "The reupload bot account is not set up yet."
        case ReuploadError.BANNED:
            return "This account cannot upload levels."
        case ReuploadError.INVALID_ID:
            return "Enter a level id from the official servers."
        case ReuploadError.ALREADY_REUPLOADED:
            return "That level is already on this server."
        case ReuploadError.IN_PROGRESS:
            return "That level is being reuploaded right now. Try again in a minute."
        case ReuploadError.RATE_LIMITED:
            return "You have used today's reuploads. Try again tomorrow."
        case ReuploadError.BUSY:
            return "The reupload tool is busy. Try again in a minute."
        case ReuploadError.UPSTREAM_NOT_FOUND:
            return "The official servers have no level with that id."
        case ReuploadError.UPSTREAM_UNAVAILABLE:
            return "The official servers are not answering. Try again in a minute."
        case ReuploadError.UPSTREAM_MALFORMED:
            return "The official servers sent something this server could not read."
        case ReuploadError.TOO_LARGE:
            return "That level is too large for this server."
        case ReuploadError.INVALID:
            return "That level could not be read."
        case (
            AdministrationError.INVALID
            | ModerationError.INVALID
            | SongError.INVALID
            | LevelError.INVALID
            | CommentError.INVALID
        ):
            return "Those values were not accepted."
        case WebError.CSRF_INVALID:
            return "The form expired. Go back, reload the page and try again."
        case WebError.CAPTCHA_FAILED:
            return "The captcha was not completed. Try again."
        case WebError.PASSWORDS_DIFFER:
            return "The passwords do not match."
        case WebError.NOT_FOUND:
            return "There is nothing here."
        case WebError.TOOL_DISABLED:
            return "This tool is switched off right now."
        case WebError.NOTHING_SELECTED:
            return "Select at least one row first."
        case WebError.INVALID_INPUT:
            return "That value could not be read."
        case IconError.UNKNOWN_KIND | IconError.UNKNOWN_ICON | IconError.INVALID_COLOUR:
            return "That icon cannot be drawn."
        case _:
            return f"Refused: {error.resolve_name()}"
