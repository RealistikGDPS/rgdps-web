from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import administration
from poltergeist_core.services import songs as core_songs
from poltergeist_core.services.songs import SongError

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import songs

router = APIRouter(prefix="/songs")

_INDEX = "/admin/songs"


@router.get("")
async def index(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    q: str = "",
    page: int = 1,
) -> Response:
    listing = await songs.listing(ctx, query=q, page=page)

    return response.render(
        request, "admin/songs.html", viewer=operator, listing=listing
    )


@router.get("/{song_id}")
async def detail(
    request: Request, song_id: int, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    song = await ctx.songs.find_by_id(song_id)

    if song is None:
        response.refuse(request, SongError.NOT_FOUND, viewer=operator)

    return response.render(request, "admin/song.html", viewer=operator, song=song)


@router.post("/disable")
async def disable(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await songs.set_disabled_many(
        ctx, actor_user_id=operator.id, song_ids=selected, disabled=True
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/enable")
async def enable(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await songs.set_disabled_many(
        ctx, actor_user_id=operator.id, song_ids=selected, disabled=False
    )

    return response.notice(response.safe_back(request, _INDEX), outcome.describe())


@router.post("/custom")
async def create(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    artist: Annotated[str, Form()],
    url: Annotated[str, Form()],
    size_mb: Annotated[float, Form()],
) -> Response:
    song = response.unwrap(
        request,
        await administration.create_song(
            ctx,
            actor_user_id=operator.id,
            name=name,
            artist_name=artist,
            url=url,
            size_bytes=songs.size_bytes(size_mb),
        ),
        viewer=operator,
    )

    return response.notice(f"{_INDEX}/{song.id}", f"Created song #{song.id}.")


@router.post("/fetch")
async def fetch(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    song_id: Annotated[int, Form()],
) -> Response:
    song = await core_songs.ensure(ctx, song_id)

    if song is None:
        return response.notice(_INDEX, f"Song #{song_id} could not be fetched.")

    return response.notice(
        f"{_INDEX}/{song.id}", f"{song.name} by {song.artist_name} is known."
    )


# NOTE: Declared last so the fixed paths above are never read as a song id.
@router.post("/{song_id}")
async def update(
    request: Request,
    song_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    artist: Annotated[str, Form()],
    url: Annotated[str, Form()],
    size_mb: Annotated[float, Form()],
) -> Response:
    response.unwrap(
        request,
        await administration.update_song(
            ctx,
            actor_user_id=operator.id,
            song_id=song_id,
            name=name,
            artist_name=artist,
            url=url,
            size_bytes=songs.size_bytes(size_mb),
        ),
        viewer=operator,
    )

    return response.notice(f"{_INDEX}/{song_id}", "Song saved.")
