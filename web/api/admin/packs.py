from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from gdformat.enums import MapPackDifficulty
from poltergeist_core.services import packs as core_packs

from web.api import forms
from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import packs

router = APIRouter(prefix="/packs")

_INDEX = "/admin/packs"


@router.get("")
async def index(
    request: Request, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    return response.render(
        request, "admin/packs.html", viewer=operator, packs=await packs.overview(ctx)
    )


@router.post("/map-packs")
async def create_pack(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    stars: Annotated[int, Form()],
    coins: Annotated[int, Form()],
    difficulty: Annotated[MapPackDifficulty, Form()],
    level_ids: Annotated[str, Form()],
    text_colour: Annotated[str, Form()] = "#ffffff",
    bar_colour: Annotated[str, Form()] = "#b48cff",
) -> Response:
    text = response.unwrap(request, forms.parse_colour(text_colour), viewer=operator)
    bar = response.unwrap(request, forms.parse_colour(bar_colour), viewer=operator)

    pack_id = response.unwrap(
        request,
        await core_packs.create_map_pack(
            ctx,
            actor_user_id=operator.id,
            name=name,
            level_ids=forms.parse_ids(level_ids),
            stars=stars,
            coins=coins,
            difficulty=difficulty,
            text_colour=text,
            bar_colour=bar,
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, f"Created map pack #{pack_id}.")


@router.post("/map-packs/remove")
async def remove_packs(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await packs.remove_packs_many(
        ctx, actor_user_id=operator.id, pack_ids=selected
    )

    return response.notice(_INDEX, outcome.describe())


@router.post("/gauntlets")
async def set_gauntlet(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    gauntlet_id: Annotated[int, Form()],
    level_ids: Annotated[str, Form()],
) -> Response:
    response.unwrap(
        request,
        await core_packs.set_gauntlet(
            ctx,
            actor_user_id=operator.id,
            gauntlet_id=gauntlet_id,
            level_ids=forms.parse_ids(level_ids),
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, "Gauntlet saved.")


@router.post("/gauntlets/remove")
async def remove_gauntlets(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await packs.remove_gauntlets_many(
        ctx, actor_user_id=operator.id, gauntlet_ids=selected
    )

    return response.notice(_INDEX, outcome.describe())
