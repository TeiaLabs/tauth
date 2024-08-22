from datetime import UTC, datetime
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from ..authz import privileges
from ..entities.models import EntityDAO
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..settings import Settings
from ..utils import creation, reading
from .models import RoleDAO
from .schemas import RoleIn, RoleIntermediate, RoleUpdate

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🏷"])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    role_in: RoleIn = Body(openapi_examples=RoleIn.get_rolein_examples()),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Creating role: {role_in}")
    logger.debug(f"Fetching entity ref from handle: {role_in.entity_handle!r}")
    entity_ref = EntityDAO.from_handle_to_ref(role_in.entity_handle)
    if not entity_ref:
        raise HTTPException(s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle")
    schema_in = RoleIntermediate(entity_ref=entity_ref, **role_in.model_dump())
    role = creation.create_one(schema_in, RoleDAO, infostar=infostar)
    return GeneratedFields(**role.model_dump(by_alias=True))


@router.get("/{role_id}", status_code=s.HTTP_200_OK)
@router.get("/{role_id}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(
    role_id: PyObjectId,
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> RoleDAO:
    logger.debug(f"Reading role {role_id!r}.")
    role = reading.read_one(
        infostar=infostar,
        model=RoleDAO,
        identifier=role_id,
    )
    return role


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
    entity_handle: Optional[str] = Query(None),
):
    logger.debug(f"Reading roles with filters: {request.query_params}")
    # Decode the URL-encoded query parameters
    decoded_query_params = {
        key: unquote(value) if isinstance(value, str) else value
        for key, value in request.query_params.items()
    }
    entity_handle_param = decoded_query_params.pop("entity_handle", None)
    if entity_handle_param:
        decoded_query_params["entity_ref.handle"] = entity_handle_param
    logger.debug(f"Decoded query params: {decoded_query_params}")
    roles = reading.read_many(
        infostar=infostar,
        model=RoleDAO,
        **decoded_query_params,
    )
    return roles


@router.patch("/{role_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.patch("/{role_id}/", status_code=s.HTTP_204_NO_CONTENT, include_in_schema=False)
async def update(
    role_id: PyObjectId,
    role_update: RoleUpdate = Body(openapi_examples=RoleUpdate.get_roleupdate_examples()),
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
        entity_ref = EntityDAO.from_handle_to_ref(role_update.entity_handle)
        if not entity_ref:
            raise HTTPException(s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle")
        role.entity_ref = entity_ref
    if role_update.permissions:
        role.permissions = role_update.permissions

    role.updated_at = datetime.now(UTC)

    role_coll = RoleDAO.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS)
    role_coll.update_one(
        {"_id": role.id},
        {"$set": role.model_dump()},
    )

@router.delete("/{role_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.delete("/{role_id}/", status_code=s.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete(
    role_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Deleting role with ID: {role_id!r}.")
    role_coll = RoleDAO.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS)
    role_coll.delete_one({"_id": role_id})
