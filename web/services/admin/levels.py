from dataclasses import dataclass
from dataclasses import replace
from enum import StrEnum

from gdformat.enums import DemonDifficulty
from gdformat.enums import SendFeature
from gdformat.enums import TimelyType
from gdformat.enums import Visibility
from poltergeist_core.resources import Level
from poltergeist_core.resources import LevelOrder
from poltergeist_core.resources import LevelSearch
from poltergeist_core.resources import LevelSuggestion
from poltergeist_core.resources import Song
from poltergeist_core.resources import User
from poltergeist_core.services import administration
from poltergeist_core.services import moderation
from poltergeist_core.services import timely
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.levels import LevelError
from poltergeist_core.services.moderation import ModerationError

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome

_QUEUE_SIZE = 50


class Order(StrEnum):
    RECENT = "recent"
    DOWNLOADS = "downloads"
    LIKES = "likes"
    FEATURED = "featured"
    RATED = "rated"


class Rated(StrEnum):
    ALL = "all"
    RATED = "rated"
    UNRATED = "unrated"


_ORDERS = {
    Order.RECENT: LevelOrder.UPLOADED,
    Order.DOWNLOADS: LevelOrder.DOWNLOADS,
    Order.LIKES: LevelOrder.LIKES,
    Order.FEATURED: LevelOrder.FEATURED,
    Order.RATED: LevelOrder.RATED,
}


@dataclass(frozen=True, slots=True)
class Filters:
    query: str
    order: Order
    rated: Rated
    creator: str
    page: int


@dataclass(frozen=True, slots=True)
class LevelListing:
    levels: list[Level]
    creators: dict[int, User]
    filters: Filters
    size: int
    total: int


@dataclass(frozen=True, slots=True)
class LevelDetail:
    level: Level
    creator: User | None
    song: Song | None


@dataclass(frozen=True, slots=True)
class SuggestionRow:
    suggestion: LevelSuggestion
    level: Level | None
    sender: User | None


@dataclass(frozen=True, slots=True)
class ReportRow:
    level: Level
    creator: User | None
    reports: int


@dataclass(frozen=True, slots=True)
class Queues:
    suggestions: list[SuggestionRow]
    reports: list[ReportRow]


def _search(filters: Filters) -> LevelSearch:
    search = LevelSearch(
        order=_ORDERS[filters.order],
        page=forms.page_index(filters.page),
        size=_common.PAGE_SIZE,
        include_all_visibilities=True,
        rated=filters.rated is Rated.RATED,
        unrated=filters.rated is Rated.UNRATED,
    )
    query = filters.query.strip()

    if query.isdecimal():
        search = replace(search, level_ids=(int(query),), order=LevelOrder.GIVEN)
    elif query:
        search = replace(search, name_prefix=query)

    if filters.creator.strip().isdecimal():
        search = replace(search, creator_ids=(int(filters.creator.strip()),))

    return search


async def _creators(ctx: AbstractContext, levels: list[Level]) -> dict[int, User]:
    users = await ctx.users.find_many_by_ids([level.user_id for level in levels])

    return {user.id: user for user in users}


async def listing(ctx: AbstractContext, filters: Filters) -> LevelListing:
    search = _search(filters)
    levels = await ctx.levels.search(search)

    return LevelListing(
        levels=levels,
        creators=await _creators(ctx, levels),
        filters=replace(filters, page=search.page + 1),
        size=search.size,
        total=await ctx.levels.count(search),
    )


async def detail(
    ctx: AbstractContext, level_id: int
) -> LevelError.OnSuccess[LevelDetail]:
    level = await ctx.levels.find_by_id(level_id)

    if level is None:
        return LevelError.NOT_FOUND

    song = None

    if level.custom_song_id is not None:
        song = await ctx.songs.find_by_id(level.custom_song_id)

    return LevelDetail(
        level=level, creator=await ctx.users.find_by_id(level.user_id), song=song
    )


async def queues(ctx: AbstractContext) -> Queues:
    pending = await ctx.suggestions.list_pending(0, _QUEUE_SIZE)
    reported = await ctx.reports.list_open_level_ids(0, _QUEUE_SIZE)
    level_ids = [entry.level_id for entry in pending] + [pair[0] for pair in reported]
    levels = {level.id: level for level in await ctx.levels.find_many_by_ids(level_ids)}
    user_ids = [entry.user_id for entry in pending] + [
        level.user_id for level in levels.values()
    ]
    users = {user.id: user for user in await ctx.users.find_many_by_ids(user_ids)}

    return Queues(
        suggestions=[
            SuggestionRow(
                suggestion=entry,
                level=levels.get(entry.level_id),
                sender=users.get(entry.user_id),
            )
            for entry in pending
        ],
        reports=[
            ReportRow(
                level=levels[level_id],
                creator=users.get(levels[level_id].user_id),
                reports=count,
            )
            for level_id, count in reported
            if level_id in levels
        ],
    )


async def rate_many(
    ctx: AbstractContext,
    *,
    actor_user_id: int,
    level_ids: list[int],
    stars: int,
    feature: SendFeature | None,
    demon: DemonDifficulty | None,
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: moderation.rate_level(
            ctx,
            actor_user_id=actor_user_id,
            level_id=level_id,
            stars=stars,
            feature=feature,
            demon=demon,
        ),
        verb="Rated",
    )


async def _rate_suggested(
    ctx: AbstractContext, *, actor_user_id: int, level_id: int
) -> ModerationError.OnSuccess[Level]:
    entry = await ctx.suggestions.find_pending(level_id)

    if entry is None:
        return ModerationError.NOT_FOUND

    return await moderation.rate_level(
        ctx,
        actor_user_id=actor_user_id,
        level_id=level_id,
        stars=entry.stars or 0,
        feature=entry.feature,
        demon=entry.demon_difficulty,
    )


async def rate_suggested_many(
    ctx: AbstractContext, *, actor_user_id: int, level_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: _rate_suggested(
            ctx, actor_user_id=actor_user_id, level_id=level_id
        ),
        verb="Rated",
    )


async def dismiss_many(
    ctx: AbstractContext, *, actor_user_id: int, level_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: administration.dismiss_suggestions(
            ctx, actor_user_id=actor_user_id, level_id=level_id
        ),
        verb="Dismissed",
    )


async def resolve_many(
    ctx: AbstractContext, *, actor_user_id: int, level_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: administration.resolve_reports(
            ctx, actor_user_id=actor_user_id, level_id=level_id
        ),
        verb="Resolved",
    )


async def set_visibility_many(
    ctx: AbstractContext,
    *,
    actor_user_id: int,
    level_ids: list[int],
    visibility: Visibility,
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: administration.set_level_visibility(
            ctx, actor_user_id=actor_user_id, level_id=level_id, visibility=visibility
        ),
        verb="Updated",
    )


async def set_locked_many(
    ctx: AbstractContext, *, actor_user_id: int, level_ids: list[int], locked: bool
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: administration.set_level_locked(
            ctx, actor_user_id=actor_user_id, level_id=level_id, locked=locked
        ),
        verb="Locked" if locked else "Unlocked",
    )


async def schedule_many(
    ctx: AbstractContext,
    *,
    actor_user_id: int,
    level_ids: list[int],
    timely_type: TimelyType,
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: timely.schedule(
            ctx, actor_user_id=actor_user_id, timely_type=timely_type, level_id=level_id
        ),
        verb="Scheduled",
    )


async def delete_many(
    ctx: AbstractContext, *, actor_user_id: int, level_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        level_ids,
        lambda level_id: administration.delete_level(
            ctx, actor_user_id=actor_user_id, level_id=level_id
        ),
        verb="Deleted",
    )
