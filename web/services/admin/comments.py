from dataclasses import dataclass
from enum import StrEnum

from poltergeist_core.resources import AccountComment
from poltergeist_core.resources import BanType
from poltergeist_core.resources import Comment
from poltergeist_core.resources import Level
from poltergeist_core.resources import User
from poltergeist_core.services import administration
from poltergeist_core.services import moderation
from poltergeist_core.services._common import AbstractContext

from web.api import forms
from web.services.admin import _common
from web.services.admin._common import BulkOutcome


class Kind(StrEnum):
    LEVEL = "levels"
    PROFILE = "profiles"


@dataclass(frozen=True, slots=True)
class CommentRow:
    id: int
    author: User | None
    author_id: int
    content: str
    likes: int
    created_at: object
    level: Level | None = None
    list_id: int | None = None
    percent: int | None = None


@dataclass(frozen=True, slots=True)
class CommentListing:
    kind: Kind
    rows: list[CommentRow]
    query: str
    author: str
    page: int
    size: int
    total: int


def _author_id(author: str) -> int | None:
    return int(author) if author.strip().isdecimal() else None


async def _level_rows(
    ctx: AbstractContext, comments: list[Comment]
) -> list[CommentRow]:
    users = {
        user.id: user
        for user in await ctx.users.find_many_by_ids([c.user_id for c in comments])
    }
    levels = {
        level.id: level
        for level in await ctx.levels.find_many_by_ids(
            [c.level_id for c in comments if c.level_id is not None]
        )
    }

    return [
        CommentRow(
            id=comment.id,
            author=users.get(comment.user_id),
            author_id=comment.user_id,
            content=comment.content,
            likes=comment.likes,
            created_at=comment.created_at,
            level=None if comment.level_id is None else levels.get(comment.level_id),
            list_id=comment.list_id,
            percent=comment.percent,
        )
        for comment in comments
    ]


async def _profile_rows(
    ctx: AbstractContext, comments: list[AccountComment]
) -> list[CommentRow]:
    users = {
        user.id: user
        for user in await ctx.users.find_many_by_ids([c.user_id for c in comments])
    }

    return [
        CommentRow(
            id=comment.id,
            author=users.get(comment.user_id),
            author_id=comment.user_id,
            content=comment.content,
            likes=comment.likes,
            created_at=comment.created_at,
        )
        for comment in comments
    ]


async def listing(
    ctx: AbstractContext, kind: Kind, *, query: str, author: str, page: int
) -> CommentListing:
    query = query.strip()
    author_id = _author_id(author)
    index = forms.page_index(page)

    match kind:
        case Kind.LEVEL:
            rows = await _level_rows(
                ctx,
                await ctx.comments.list_recent(
                    query=query, user_id=author_id, page=index, size=_common.PAGE_SIZE
                ),
            )
            total = await ctx.comments.count_recent(query=query, user_id=author_id)
        case Kind.PROFILE:
            rows = await _profile_rows(
                ctx,
                await ctx.account_comments.list_recent(
                    query=query, user_id=author_id, page=index, size=_common.PAGE_SIZE
                ),
            )
            total = await ctx.account_comments.count_recent(
                query=query, user_id=author_id
            )

    return CommentListing(
        kind=kind,
        rows=rows,
        query=query,
        author=author.strip(),
        page=index + 1,
        size=_common.PAGE_SIZE,
        total=total,
    )


async def delete_many(
    ctx: AbstractContext, kind: Kind, *, actor_user_id: int, comment_ids: list[int]
) -> BulkOutcome:
    match kind:
        case Kind.LEVEL:
            return await _common.run_bulk(
                comment_ids,
                lambda comment_id: administration.delete_comment(
                    ctx, actor_user_id=actor_user_id, comment_id=comment_id
                ),
                verb="Deleted",
            )
        case Kind.PROFILE:
            return await _common.run_bulk(
                comment_ids,
                lambda comment_id: administration.delete_account_comment(
                    ctx, actor_user_id=actor_user_id, comment_id=comment_id
                ),
                verb="Deleted",
            )


async def _author_of(ctx: AbstractContext, kind: Kind, comment_id: int) -> int | None:
    match kind:
        case Kind.LEVEL:
            comment = await ctx.comments.find_by_id(comment_id)

            return None if comment is None else comment.user_id
        case Kind.PROFILE:
            post = await ctx.account_comments.find_by_id(comment_id)

            return None if post is None else post.user_id


async def _author_ids(
    ctx: AbstractContext, kind: Kind, comment_ids: list[int]
) -> list[int]:
    """The authors are looked up here rather than trusted from the form."""

    authors = [await _author_of(ctx, kind, comment_id) for comment_id in comment_ids]

    return list(dict.fromkeys(author for author in authors if author is not None))


async def ban_authors(
    ctx: AbstractContext,
    kind: Kind,
    *,
    actor_user_id: int,
    comment_ids: list[int],
    days: int | None,
    reason: str,
) -> BulkOutcome:
    return await _common.run_bulk(
        await _author_ids(ctx, kind, comment_ids),
        lambda user_id: moderation.ban(
            ctx,
            actor_user_id=actor_user_id,
            target_user_id=user_id,
            ban_type=BanType.COMMENT,
            days=days,
            reason=reason,
        ),
        verb="Comment-banned",
    )
