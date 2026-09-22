from dataclasses import dataclass

from poltergeist_core.resources import DemonListRecord
from poltergeist_core.resources import RecordStatus
from poltergeist_core.services import demon_list
from poltergeist_core.services import is_error
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.demon_list import DemonList
from poltergeist_core.services.demon_list import DemonListError
from poltergeist_core.services.demon_list import PlacementDetail


@dataclass(frozen=True, slots=True)
class LevelPage:
    """The listed level with what the viewer already has on it, so the submit
    form can say why it is closed before the service refuses."""

    detail: PlacementDetail
    # The whole list, for the side navigation.
    listing: DemonList
    pending: DemonListRecord | None
    approved: DemonListRecord | None
    rejected: DemonListRecord | None


async def level_page(
    ctx: AbstractContext, level_id: int, viewer_user_id: int | None
) -> DemonListError.OnSuccess[LevelPage]:
    detail = await demon_list.placement_detail(ctx, level_id=level_id)

    if is_error(detail):
        return detail

    listing = await demon_list.overview(ctx)

    if viewer_user_id is None:
        return LevelPage(
            detail=detail, listing=listing, pending=None, approved=None, rejected=None
        )

    placement_id = detail.placement.id
    records = ctx.demon_list_records
    recent = await records.list_page(
        status=None, placement_id=placement_id, user_id=viewer_user_id, page=0, size=1
    )
    latest = recent[0] if recent else None

    return LevelPage(
        detail=detail,
        listing=listing,
        pending=await records.find_pending(placement_id, viewer_user_id),
        approved=await records.find_approved(placement_id, viewer_user_id),
        # A rejection is only worth showing while it is the viewer's latest word.
        rejected=latest
        if latest is not None and latest.status is RecordStatus.REJECTED
        else None,
    )
