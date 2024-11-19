import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from ...authz import privileges
from ...entities.models import EntityDAO
from ...schemas import Infostar
from ...schemas.gen_fields import GeneratedFields
from ...settings import Settings
from ...utils import creation, reading
from ..roles.models import RoleDAO
from .models import PermissionDAO
from .schemas import PermissionIn, PermissionIntermediate, PermissionUpdate

service_name = Path(__file__).parents[1].name
router = APIRouter(
    prefix=f"/{service_name}/permissions", tags=[service_name + " 🔐"]
)


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    permission_in: PermissionIn = Body(
        openapi_examples=PermissionIn.get_permission_create_examples()
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Creating permission: {permission_in}.")
    logger.debug(
        f"Fetching entity ref from handle: {permission_in.entity_ref!r}"
    )
    entity_ref = EntityDAO.from_handle_to_ref(
        permission_in.entity_ref.handle,
        owner_handle=permission_in.entity_ref.owner_handle,
    )
    if not entity_ref:
        raise HTTPException(
            s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle"
        )
    schema_in = PermissionIntermediate(
        entity_ref=entity_ref,
        **permission_in.model_dump(exclude={"entity_ref"}),
    )
    role = creation.create_one(schema_in, PermissionDAO, infostar=infostar)
    return GeneratedFields(**role.model_dump(by_alias=True))


@router.get("/{permission_id}", status_code=s.HTTP_200_OK)
@router.get(
    "/{permission_id}/", status_code=s.HTTP_200_OK, include_in_schema=False
)
async def read_one(
    permission_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> PermissionDAO:
    logger.debug(f"Reading permission {permission_id!r}.")
    role = reading.read_one(
        infostar=infostar,
        model=PermissionDAO,
        identifier=permission_id,
    )
    return role


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: str | None = Query(None),
    entity_handle: str | None = Query(None),
):
    logger.debug(f"Reading permissions with filters: {request.query_params}")
    # Decode the URL-encoded query parameters
    decoded_query_params = {
        key: unquote(value) if isinstance(value, str) else value
        for key, value in request.query_params.items()
    }
    if name:
        decoded_query_params["name"] = {  # type: ignore
            "$regex": re.escape(name),
            "$options": "i",
        }
    if entity_handle:
        handle = decoded_query_params.pop("entity_handle")
        decoded_query_params["entity_ref.handle"] = handle
    logger.debug(f"Decoded query params: {decoded_query_params}")
    roles = reading.read_many(
        infostar=infostar,
        model=PermissionDAO,
        **decoded_query_params,
    )
    return roles


@router.patch("/{permission_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.patch(
    "/{permission_id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def update(
    permission_id: PyObjectId,
    permission_update: PermissionUpdate = Body(
        openapi_examples=PermissionUpdate.get_permission_update_examples()
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Updating permission with ID: {permission_id!r}.")
    permission = reading.read_one(
        infostar=infostar,
        model=PermissionDAO,
        identifier=permission_id,
    )

    if permission_update.name:
        permission.name = permission_update.name
    if permission_update.description:
        permission.description = permission_update.description
    if permission_update.entity_ref:
        entity_ref = EntityDAO.from_handle_to_ref(
            permission_update.entity_ref.handle,
            permission_update.entity_ref.owner_handle,
        )
        if not entity_ref:
            raise HTTPException(
                s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle"
            )
        permission.entity_ref = entity_ref

    permission.updated_at = datetime.now(UTC)

    role_coll = PermissionDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    role_coll.update_one(
        {"_id": permission.id},
        {"$set": permission.model_dump()},
    )


@router.delete("/{permission_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.delete(
    "/{permission_id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def delete(
    permission_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    # We need to block deleting a permission if a role is using it.
    logger.debug(f"Deleting permission with ID: {permission_id!r}.")
    logger.debug(
        f"Checking if permission {permission_id!r} is used by a role."
    )
    roles = reading.read_many(
        infostar=infostar,
        model=RoleDAO,
        **{"permissions": permission_id},
    )
    if roles:
        role_names = [role.name for role in roles]
        logger.debug(
            f"Permission {permission_id!r} is used by role(s): {role_names}."
        )
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete permission {str(permission_id)!r} because it is used by role(s): {role_names}.",
        )

    role_coll = PermissionDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    role_coll.delete_one({"_id": permission_id})
