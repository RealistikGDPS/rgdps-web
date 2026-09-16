from dataclasses import dataclass
from enum import StrEnum

from poltergeist_core.resources import ServerSettings

from web.errors import WebError


class Tool(StrEnum):
    SONG_REUPLOAD = "song-reupload"
    LEVEL_REUPLOAD = "level-reupload"


@dataclass(frozen=True, slots=True)
class ToolCard:
    tool: Tool
    title: str
    blurb: str
    enabled: bool
    ready: bool


def enabled(site: ServerSettings, tool: Tool) -> bool:
    match tool:
        case Tool.SONG_REUPLOAD:
            return site.song_reupload_enabled
        case Tool.LEVEL_REUPLOAD:
            return site.level_reupload_enabled


def require(site: ServerSettings, tool: Tool) -> WebError.OnSuccess[None]:
    if not enabled(site, tool):
        return WebError.TOOL_DISABLED

    return None


def cards(site: ServerSettings) -> list[ToolCard]:
    return [
        ToolCard(
            tool=Tool.SONG_REUPLOAD,
            title="Song reupload",
            blurb="Bring a song onto the server so it can be used in your levels.",
            enabled=enabled(site, Tool.SONG_REUPLOAD),
            ready=False,
        ),
        ToolCard(
            tool=Tool.LEVEL_REUPLOAD,
            title="Level reupload",
            blurb=(
                "Copy a level from the official servers onto this server, "
                "published by the reupload bot."
            ),
            enabled=enabled(site, Tool.LEVEL_REUPLOAD),
            ready=True,
        ),
    ]
