from datetime import datetime
from datetime import time

from web.errors import WebError

_ID_SEPARATORS = str.maketrans({"\n": ",", " ": ",", ";": ","})
_COLOUR_DIGITS = 6
_DATE_FORMAT = "%Y-%m-%d"


def parse_ids(text: str) -> list[int]:
    """Comma, space or newline separated ids; anything else is skipped."""

    parts = text.translate(_ID_SEPARATORS).split(",")

    return [int(part) for part in parts if part.strip().isdecimal()]


def parse_colour(text: str) -> WebError.OnSuccess[int]:
    """`#rrggbb` from a colour input into the packed integer the game stores."""

    digits = text.strip().removeprefix("#")

    if len(digits) != _COLOUR_DIGITS:
        return WebError.INVALID_INPUT

    try:
        return int(digits, 16)
    except ValueError:
        return WebError.INVALID_INPUT


def parse_date_end(text: str) -> WebError.OnSuccess[datetime | None]:
    """A date input as the last second of that UTC day; empty means never."""

    if not text.strip():
        return None

    try:
        day = datetime.strptime(text.strip(), _DATE_FORMAT).date()
    except ValueError:
        return WebError.INVALID_INPUT

    return datetime.combine(day, time.max.replace(microsecond=0))


def page_index(page: int) -> int:
    """Pages are 1-based in URLs and 0-based in every repository."""

    return max(page, 1) - 1
