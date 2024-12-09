from collections.abc import Iterable

from fastapi import HTTPException, Request
from redbaby.pyobjectid import PyObjectId

from tauth.authn.tauth_keys.models import TauthTokenDAO
from tauth.authz.permissions.controllers import (
    read_many_permissions,
    read_permissions_from_roles,
)
from tauth.authz.permissions.schemas import PermissionContext
from tauth.schemas.infostar import Infostar

from ..authn.tauth_keys.utils import TauthKeyParseError, parse_key


async def get_request_context(request: Request) -> dict:
    context = {}
    context["query"] = dict(request.query_params)
    context["headers"] = dict(request.headers)
    context["path"] = request.path_params
    context["method"] = request.method
    context["url"] = str(request.url)

    if await request.body():
        context["body"] = await request.json()

    return context


def get_permissions_set(
    roles: Iterable[PyObjectId], entity_permissions: list[PyObjectId]
) -> set[PermissionContext]:
    s = get_permission_set_from_roles(roles)
    s2 = read_many_permissions(entity_permissions)

    return s.union(s2)


def get_permission_set_from_roles(
    roles: Iterable[PyObjectId],
) -> set[PermissionContext]:
    permissions = read_permissions_from_roles(roles)
    s = set(
        context for contexts in permissions.values() for context in contexts
    )
    return s


def get_allowed_permissions(request: Request) -> set[PermissionContext] | None:
    infostar: Infostar = request.state.infostar
    # If it is an impersonation, do not use token permissions
    if infostar.authprovider_type == "tauth-key" and infostar.original is None:
        token = request.headers.get("Authorization")
        assert token
        token_obj = resolve_token(token)
        return get_permission_set_from_roles(token_obj.roles)
    return None


def resolve_token(token: str):

    token = token.split()[-1]
    try:
        id, _ = parse_key(token)
    except TauthKeyParseError:
        raise HTTPException(status_code=401, detail="Invalid tauth key format")

    return TauthTokenDAO.find_one_token(id)
