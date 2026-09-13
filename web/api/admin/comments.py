from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import comments
from web.services.admin.comments import Kind

router = APIRouter(prefix="/comments")


@router.get("")
async def index() -> Response:
    return response.redirect(f"/admin/comments/{Kind.LEVEL}")


@router.get("/{kind}")
async def listing(
    request: Request,
    kind: Kind,
    ctx: RequiresContext,
    operator: RequiresOperator,
    q: str = "",
    author: str = "",
    page: int = 1,
) -> Response:
    listing = await comments.listing(ctx, kind, query=q, author=author, page=page)

    return response.render(
        request,
        "admin/comments.html",
        viewer=operator,
        listing=listing,
        kinds=list(Kind),
    )


@router.post("/{kind}/delete")
async def delete(
    request: Request,
    kind: Kind,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await comments.delete_many(
        ctx, kind, actor_user_id=operator.id, comment_ids=selected
    )

    return response.notice(
        response.safe_back(request, f"/admin/comments/{kind}"), outcome.describe()
    )


@router.post("/{kind}/ban-authors")
async def ban_authors(
    request: Request,
    kind: Kind,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    permanent: Annotated[bool, Form()] = False,
    days: Annotated[int, Form()] = 3,
    reason: Annotated[str, Form()] = "",
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await comments.ban_authors(
        ctx,
        kind,
        actor_user_id=operator.id,
        comment_ids=selected,
        days=None if permanent else max(days, 1),
        reason=reason.strip(),
    )

    return response.notice(
        response.safe_back(request, f"/admin/comments/{kind}"), outcome.describe()
    )
