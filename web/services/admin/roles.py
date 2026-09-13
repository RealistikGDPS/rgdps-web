from dataclasses import dataclass

from poltergeist_core.resources import Role
from poltergeist_core.resources import User
from poltergeist_core.services._common import AbstractContext
from poltergeist_core.services.roles import RoleError

_MEMBERS_SHOWN = 60


@dataclass(frozen=True, slots=True)
class RoleRow:
    role: Role
    permissions: list[str]
    members: int


@dataclass(frozen=True, slots=True)
class RoleDetail:
    role: Role
    permissions: list[str]
    members: list[User]
    member_count: int


async def listing(ctx: AbstractContext) -> list[RoleRow]:
    return [
        RoleRow(
            role=role,
            permissions=await ctx.roles.list_permissions(role.id),
            members=await ctx.roles.count_members(role.id),
        )
        for role in await ctx.roles.list_all()
    ]


async def detail(ctx: AbstractContext, role_id: int) -> RoleError.OnSuccess[RoleDetail]:
    role = await ctx.roles.find_by_id(role_id)

    if role is None:
        return RoleError.NOT_FOUND

    member_ids = await ctx.roles.list_member_ids(role_id)

    return RoleDetail(
        role=role,
        permissions=await ctx.roles.list_permissions(role_id),
        members=await ctx.users.find_many_by_ids(member_ids[:_MEMBERS_SHOWN]),
        member_count=len(member_ids),
    )


def parse_permissions(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]
