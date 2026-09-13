from dataclasses import dataclass

from gdformat.enums import RewardItem
from poltergeist_core.resources import Quest
from poltergeist_core.resources import SecretReward
from poltergeist_core.resources import SecretRewardItem
from poltergeist_core.services import administration
from poltergeist_core.services._common import AbstractContext

from web.services.admin import _common
from web.services.admin._common import BulkOutcome

ITEM_SLOTS = 3


@dataclass(frozen=True, slots=True)
class CodeRow:
    reward: SecretReward
    items: list[SecretRewardItem]
    claims: int


@dataclass(frozen=True, slots=True)
class Rewards:
    quests: list[Quest]
    codes: list[CodeRow]


async def overview(ctx: AbstractContext) -> Rewards:
    rewards = await ctx.secret_rewards.list_all()

    return Rewards(
        quests=await ctx.quests.list_active(),
        codes=[
            CodeRow(
                reward=reward,
                items=await ctx.secret_rewards.list_items(reward.id),
                claims=await ctx.secret_rewards.count_claims(reward.id),
            )
            for reward in rewards
        ],
    )


def items_from_slots(
    items: list[int | None], amounts: list[int]
) -> list[tuple[RewardItem, int]]:
    """Pairs the code form's item slots with their amounts, skipping empty slots."""

    picks: list[tuple[RewardItem, int]] = []

    for item, amount in zip(items, amounts, strict=True):
        if item is None or item not in RewardItem or amount <= 0:
            continue

        picks.append((RewardItem(item), amount))

    return picks


async def remove_quests_many(
    ctx: AbstractContext, *, actor_user_id: int, quest_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        quest_ids,
        lambda quest_id: administration.remove_quest(
            ctx, actor_user_id=actor_user_id, quest_id=quest_id
        ),
        verb="Removed",
    )


async def remove_codes_many(
    ctx: AbstractContext, *, actor_user_id: int, reward_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        reward_ids,
        lambda reward_id: administration.remove_secret_reward(
            ctx, actor_user_id=actor_user_id, reward_id=reward_id
        ),
        verb="Removed",
    )
