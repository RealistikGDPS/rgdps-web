from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from gdformat.enums import ChestType
from gdformat.enums import QuestItem
from poltergeist_core.services import administration

from web.api import forms
from web.api import response
from web.api.admin._common import SelectedIds
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services import admin
from web.services.admin import rewards

router = APIRouter(prefix="/rewards")

_INDEX = "/admin/rewards"


@router.get("")
async def index(
    request: Request, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    return response.render(
        request,
        "admin/rewards.html",
        viewer=operator,
        rewards=await rewards.overview(ctx),
        slots=range(1, rewards.ITEM_SLOTS + 1),
    )


@router.post("/quests")
async def create_quest(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    item: Annotated[QuestItem, Form()],
    amount: Annotated[int, Form()],
    diamonds: Annotated[int, Form()],
) -> Response:
    quest_id = response.unwrap(
        request,
        await administration.create_quest(
            ctx,
            actor_user_id=operator.id,
            item=item,
            amount=amount,
            diamonds=diamonds,
            name=name,
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, f"Created quest #{quest_id}.")


@router.post("/quests/remove")
async def remove_quests(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await rewards.remove_quests_many(
        ctx, actor_user_id=operator.id, quest_ids=selected
    )

    return response.notice(_INDEX, outcome.describe())


@router.post("/codes")
async def create_code(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    reward_key: Annotated[str, Form()],
    chest_type: Annotated[ChestType, Form()],
    max_claims: Annotated[int, Form()] = 0,
    expires_on: Annotated[str, Form()] = "",
    item_1: Annotated[int | None, Form()] = None,
    amount_1: Annotated[int, Form()] = 0,
    item_2: Annotated[int | None, Form()] = None,
    amount_2: Annotated[int, Form()] = 0,
    item_3: Annotated[int | None, Form()] = None,
    amount_3: Annotated[int, Form()] = 0,
) -> Response:
    expires_at = response.unwrap(
        request, forms.parse_date_end(expires_on), viewer=operator
    )

    reward_id = response.unwrap(
        request,
        await administration.create_secret_reward(
            ctx,
            actor_user_id=operator.id,
            reward_key=reward_key,
            chest_type=chest_type,
            items=rewards.items_from_slots(
                [item_1, item_2, item_3], [amount_1, amount_2, amount_3]
            ),
            max_claims=max_claims or None,
            expires_at=expires_at,
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, f"Created vault code #{reward_id}.")


@router.post("/codes/remove")
async def remove_codes(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    ids: SelectedIds = None,
) -> Response:
    selected = response.unwrap(request, admin.selection(ids), viewer=operator)

    outcome = await rewards.remove_codes_many(
        ctx, actor_user_id=operator.id, reward_ids=selected
    )

    return response.notice(_INDEX, outcome.describe())
