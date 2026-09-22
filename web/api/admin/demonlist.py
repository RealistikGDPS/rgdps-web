from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import demon_list

from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import demonlist

router = APIRouter(prefix="/demonlist")

_INDEX = "/admin/demonlist"
_RECORDS = "/admin/demonlist/records"


@router.get("")
async def index(
    request: Request, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    placements = await demonlist.placements(ctx)

    return response.render(
        request, "admin/demonlist.html", viewer=operator, placements=placements
    )


@router.post("/place")
async def place(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    level_id: Annotated[int, Form()],
    position: Annotated[str, Form()] = "",
    requirement: Annotated[int, Form()] = 100,
    video_url: Annotated[str, Form()] = "",
) -> Response:
    placement_id = response.unwrap(
        request,
        await demon_list.place(
            ctx,
            actor_user_id=operator.id,
            level_id=level_id,
            position=int(position) if position.strip().isdecimal() else None,
            requirement=requirement,
            video_url=video_url.strip(),
        ),
        viewer=operator,
    )

    return response.notice(
        f"{_INDEX}/{placement_id}", f"Placed level {level_id} on the list."
    )


@router.get("/records")
async def records(
    request: Request,
    ctx: RequiresContext,
    operator: RequiresOperator,
    status: str = "pending",
    level: str = "",
    user: str = "",
    page: int = 1,
) -> Response:
    listing = await demonlist.records(
        ctx, status=status, level=level, user=user, page=page
    )

    return response.render(
        request, "admin/demonlist_records.html", viewer=operator, listing=listing
    )


@router.post("/records/approve")
async def approve(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await demonlist.approve_many(
        ctx, actor_user_id=operator.id, record_ids=selected
    )

    return response.notice(response.safe_back(request, _RECORDS), outcome.describe())


@router.post("/records/reject")
async def reject(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
    note: Annotated[str, Form()] = "",
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await demonlist.reject_many(
        ctx, actor_user_id=operator.id, record_ids=selected, note=note.strip()
    )

    return response.notice(response.safe_back(request, _RECORDS), outcome.describe())


@router.post("/records/delete")
async def delete(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await demonlist.delete_many(
        ctx, actor_user_id=operator.id, record_ids=selected
    )

    return response.notice(response.safe_back(request, _RECORDS), outcome.describe())


@router.post("/records/add")
async def add_record(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    placement_id: Annotated[int, Form()],
    user_id: Annotated[int, Form()],
    percent: Annotated[int, Form()] = 100,
    video_url: Annotated[str, Form()] = "",
) -> Response:
    record_id = response.unwrap(
        request,
        await demon_list.add_record(
            ctx,
            actor_user_id=operator.id,
            placement_id=placement_id,
            user_id=user_id,
            percent=percent,
            video_url=video_url.strip(),
        ),
        viewer=operator,
    )

    return response.notice(
        response.safe_back(request, _RECORDS), f"Added record #{record_id}."
    )


@router.get("/{placement_id}")
async def placement(
    request: Request,
    placement_id: int,
    ctx: RequiresContext,
    operator: RequiresOperator,
) -> Response:
    page = response.unwrap(
        request, await demonlist.placement(ctx, placement_id), viewer=operator
    )

    return response.render(
        request, "admin/demonlist_placement.html", viewer=operator, page=page
    )


@router.post("/{placement_id}/move")
async def move(
    request: Request,
    placement_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    position: Annotated[int, Form()],
) -> Response:
    response.unwrap(
        request,
        await demon_list.move(
            ctx, actor_user_id=operator.id, placement_id=placement_id, position=position
        ),
        viewer=operator,
    )

    return response.notice(
        response.safe_back(request, _INDEX), f"Moved to #{position}."
    )


@router.post("/{placement_id}/update")
async def update(
    request: Request,
    placement_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    requirement: Annotated[int, Form()] = 100,
    video_url: Annotated[str, Form()] = "",
) -> Response:
    response.unwrap(
        request,
        await demon_list.update_placement(
            ctx,
            actor_user_id=operator.id,
            placement_id=placement_id,
            requirement=requirement,
            video_url=video_url.strip(),
        ),
        viewer=operator,
    )

    return response.notice(
        response.safe_back(request, f"{_INDEX}/{placement_id}"), "Placement updated."
    )


@router.post("/{placement_id}/remove")
async def remove(
    request: Request,
    placement_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
) -> Response:
    response.unwrap(
        request,
        await demon_list.remove(
            ctx, actor_user_id=operator.id, placement_id=placement_id
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, "Removed from the list.")
