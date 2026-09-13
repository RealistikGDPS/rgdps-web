from dataclasses import dataclass

from poltergeist_core.resources import Gauntlet
from poltergeist_core.resources import MapPack
from poltergeist_core.services import administration
from poltergeist_core.services._common import AbstractContext

from web.services.admin import _common
from web.services.admin._common import BulkOutcome


@dataclass(frozen=True, slots=True)
class PackRow:
    pack: MapPack
    level_ids: list[int]


@dataclass(frozen=True, slots=True)
class Packs:
    packs: list[PackRow]
    gauntlets: list[Gauntlet]


async def overview(ctx: AbstractContext) -> Packs:
    packs = await ctx.map_packs.list_all()
    level_ids = await ctx.map_packs.list_level_ids_many([pack.id for pack in packs])

    return Packs(
        packs=[
            PackRow(pack=pack, level_ids=level_ids.get(pack.id, [])) for pack in packs
        ],
        gauntlets=await ctx.gauntlets.list_all(),
    )


async def remove_packs_many(
    ctx: AbstractContext, *, actor_user_id: int, pack_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        pack_ids,
        lambda pack_id: administration.remove_map_pack(
            ctx, actor_user_id=actor_user_id, pack_id=pack_id
        ),
        verb="Removed",
    )


async def remove_gauntlets_many(
    ctx: AbstractContext, *, actor_user_id: int, gauntlet_ids: list[int]
) -> BulkOutcome:
    return await _common.run_bulk(
        gauntlet_ids,
        lambda gauntlet_id: administration.remove_gauntlet(
            ctx, actor_user_id=actor_user_id, gauntlet_id=gauntlet_id
        ),
        verb="Removed",
    )
