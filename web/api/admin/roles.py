from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi import Response
from poltergeist_core.services import administration

from web.api import response
from web.api.dependencies import RequiresContext
from web.api.dependencies import RequiresCsrf
from web.api.dependencies import RequiresOperator
from web.api.dependencies import RequiresTransaction
from web.services.admin import roles

router = APIRouter(prefix="/roles")

_INDEX = "/admin/roles"


@router.get("")
async def index(
    request: Request, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    return response.render(
        request, "admin/roles.html", viewer=operator, rows=await roles.listing(ctx)
    )


@router.get("/{role_id}")
async def detail(
    request: Request, role_id: int, ctx: RequiresContext, operator: RequiresOperator
) -> Response:
    detail = response.unwrap(request, await roles.detail(ctx, role_id), viewer=operator)

    return response.render(request, "admin/role.html", viewer=operator, detail=detail)


@router.post("")
async def create(
    request: Request,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    priority: Annotated[int, Form()],
    description: Annotated[str, Form()] = "",
    permissions: Annotated[str, Form()] = "",
) -> Response:
    role = response.unwrap(
        request,
        await administration.create_role(
            ctx,
            actor_user_id=operator.id,
            name=name,
            description=description,
            priority=priority,
            granted=roles.parse_permissions(permissions),
        ),
        viewer=operator,
    )

    return response.notice(f"{_INDEX}/{role.id}", f"Created role {role.name}.")


@router.post("/{role_id}")
async def update(
    request: Request,
    role_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
    name: Annotated[str, Form()],
    priority: Annotated[int, Form()],
    description: Annotated[str, Form()] = "",
    permissions: Annotated[str, Form()] = "",
) -> Response:
    response.unwrap(
        request,
        await administration.update_role(
            ctx,
            actor_user_id=operator.id,
            role_id=role_id,
            name=name,
            description=description,
            priority=priority,
            granted=roles.parse_permissions(permissions),
        ),
        viewer=operator,
    )

    return response.notice(
        f"{_INDEX}/{role_id}", "Role saved. Members' permissions were refreshed."
    )


@router.post("/{role_id}/remove")
async def remove(
    request: Request,
    role_id: int,
    ctx: RequiresTransaction,
    operator: RequiresOperator,
    _: RequiresCsrf,
) -> Response:
    response.unwrap(
        request,
        await administration.remove_role(
            ctx, actor_user_id=operator.id, role_id=role_id
        ),
        viewer=operator,
    )

    return response.notice(_INDEX, "Role removed.")
