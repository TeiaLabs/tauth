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
from ..permissions.models import PermissionDAO
from ..permissions.schemas import PermissionOut
from .models import RoleDAO
from .schemas import RoleIn, RoleIntermediate, RoleOut, RoleUpdate

service_name = Path(__file__).parents[1].name
router = APIRouter(
    prefix=f"/{service_name}/roles", tags=[service_name + " 🔐"]
)


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    role_in: RoleIn = Body(openapi_examples=RoleIn.get_role_examples()),
    infostar: Infostar = Depends(privileges.is_valid_admin),
) -> GeneratedFields:
    logger.debug(f"Creating role: {role_in}")
    logger.debug(f"Fetching entity ref from handle: {role_in.entity_ref!r}")
    entity_ref = EntityDAO.from_handle_to_ref(
        handle=role_in.entity_ref.handle,
        owner_handle=role_in.entity_ref.owner_handle,
    )
    if not entity_ref:
        raise HTTPException(
            s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle"
        )

    permission_ids = []
    if role_in.permissions:
        logger.debug("Validating permissions for role creation.")
        permissions_coll = PermissionDAO.collection(
            alias=Settings.get().REDBABY_ALIAS
        )
        permission_list = permissions_coll.find(
            {
                "name": {"$in": role_in.permissions},
                "entity_ref.handle": role_in.entity_ref.handle,
            }
        )
        permission_list = list(permission_list)
        if len(role_in.permissions) != len(permission_list):
            logger.error(
                f"Invalid permissions for role creation: {role_in.permissions!r} - {permission_list!r}."
            )
            raise HTTPException(
                status_code=s.HTTP_400_BAD_REQUEST,
                detail="Invalid permissions provided.",
            )
        permission_names = [p["name"] for p in permission_list]
        permission_ids = [p["_id"] for p in permission_list]
        logger.debug(
            f"Permissions: {list(zip(permission_names, permission_ids, strict=False))}."
        )

    role_in.permissions = permission_ids
    schema_in = RoleIntermediate(
        entity_ref=entity_ref, **role_in.model_dump(exclude={"entity_ref"})
    )
    role = creation.create_one(schema_in, RoleDAO, infostar=infostar)
    return GeneratedFields(**role.model_dump(by_alias=True))


@router.get("/{role_id}", status_code=s.HTTP_200_OK)
@router.get("/{role_id}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(
    role_id: PyObjectId,
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> RoleOut:
    logger.debug(f"Reading role {role_id!r}.")
    role = reading.read_one(
        infostar=infostar,
        model=RoleDAO,
        identifier=role_id,
    )

    # Decode permissions and entity handle
    permission_coll = PermissionDAO.collection(
        alias=Settings.get().REDBABY_ALIAS
    )
    permissions = []
    if role.permissions:
        permission_list = permission_coll.find(
            {"_id": {"$in": role.permissions}}
        )
        permissions = [PermissionOut(**p) for p in permission_list]
        permissions = sorted(permissions, key=lambda p: p.name)
    role_out = RoleOut(
        **role.model_dump(
            by_alias=True, exclude={"permissions", "entity_ref"}
        ),
        permissions=permissions,
        entity_handle=role.entity_ref.handle,
    )
    return role_out


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: str | None = Query(None),
    entity_handle: str | None = Query(None),
) -> list[RoleOut]:
    logger.debug(f"Reading roles with filters: {request.query_params}")
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
        model=RoleDAO,
        **decoded_query_params,
    )
    logger.debug(f"Roles: {roles}")

    # Decode permissions and entity handle
    roles_out = []
    permission_coll = PermissionDAO.collection(
        alias=Settings.get().REDBABY_ALIAS
    )
    for role in roles:
        permissions = []
        if role.permissions:
            permission_list = permission_coll.find(
                {"_id": {"$in": role.permissions}}
            )
            permissions = [PermissionOut(**p) for p in permission_list]
            permissions = sorted(permissions, key=lambda p: p.name)
        role_out = RoleOut(
            **role.model_dump(
                by_alias=True, exclude={"permissions", "entity_ref"}
            ),
            permissions=permissions,
            entity_handle=role.entity_ref.handle,
        )
        roles_out.append(role_out)
    return roles_out


@router.patch("/{role_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.patch(
    "/{role_id}/", status_code=s.HTTP_204_NO_CONTENT, include_in_schema=False
)
async def update(
    role_id: PyObjectId,
    role_update: RoleUpdate = Body(
        openapi_examples=RoleUpdate.get_roleupdate_examples()
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Updating role with ID: {role_id!r}.")
    role = reading.read_one(
        infostar=infostar,
        model=RoleDAO,
        identifier=role_id,
    )

    if role_update.name:
        role.name = role_update.name
    if role_update.description:
        role.description = role_update.description
    if role_update.entity_handle:
        entity_ref = EntityDAO.from_handle_to_ref(
            handle=role_update.entity_handle.handle,
            owner_handle=role_update.entity_handle.owner_handle,
        )
        if not entity_ref:
            raise HTTPException(
                s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle"
            )
        role.entity_ref = entity_ref
    if role_update.permissions:
        permissions = [PyObjectId(p) for p in role_update.permissions]
        role.permissions = permissions

    role.updated_at = datetime.now(UTC)

    role_coll = RoleDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    role_coll.update_one(
        {"_id": role.id},
        {"$set": role.model_dump()},
    )


@router.delete("/{role_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.delete(
    "/{role_id}/", status_code=s.HTTP_204_NO_CONTENT, include_in_schema=False
)
async def delete(
    role_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Checking if entities are using role with ID: {role_id!r}.")
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    entity_count = entity_coll.count_documents({"roles.id": role_id})
    logger.debug(f"Role {role_id!r} used by {entity_count} entities.")
    if entity_count:
        raise HTTPException(
            s.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role that is in use by entities (used by {entity_count}).",
        )

    logger.debug(f"Deleting role with ID: {role_id!r}.")
    role_coll = RoleDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = role_coll.delete_one({"_id": role_id})
    if res.deleted_count != 1:
        raise HTTPException(
            s.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id!r} not found.",
        )
    logger.debug(f"Delete result: {res}")
