from dataclasses import dataclass

from poltergeist_core.resources import Song
from poltergeist_core.services import administration
from poltergeist_core.services._common import AbstractContext

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome

BYTES_PER_MEGABYTE = 1_048_576


@dataclass(frozen=True, slots=True)
class SongListing:
    songs: list[Song]
    query: str
    page: int
    size: int
    total: int


async def listing(ctx: AbstractContext, *, query: str, page: int) -> SongListing:
    query = query.strip()
    index = forms.page_index(page)

    return SongListing(
        songs=await ctx.songs.list_page(
            query=query, page=index, size=_common.PAGE_SIZE
        ),
        query=query,
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=await ctx.songs.count_page(query=query),
    )


def size_bytes(megabytes: float) -> int:
    return int(megabytes * BYTES_PER_MEGABYTE)


async def set_disabled_many(
    ctx: AbstractContext, *, actor_user_id: int, song_ids: list[int], disabled: bool
) -> BulkOutcome:
    return await _common.run_bulk(
        song_ids,
        lambda song_id: administration.set_song_disabled(
            ctx, actor_user_id=actor_user_id, song_id=song_id, disabled=disabled
        ),
        verb="Disabled" if disabled else "Enabled",
    )
