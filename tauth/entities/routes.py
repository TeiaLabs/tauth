import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi import Path as PathParam
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from ..authz import privileges
from ..authz.roles.models import RoleDAO
from ..authz.roles.schemas import RoleRef
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..settings import Settings
from ..utils import creation, reading
from .models import EntityDAO
from .schemas import EntityIn, EntityIntermediate

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 👥💻🏢"])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    body: EntityIn = Body(openapi_examples=EntityIn.get_entity_examples()),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    if body.owner_handle:
        owner_ref = EntityDAO.from_handle_to_ref(body.owner_handle)
    else:
        owner_ref = None
    schema_in = EntityIntermediate(owner_ref=owner_ref, **body.model_dump())
    entity = creation.create_one(schema_in, EntityDAO, infostar)
    return GeneratedFields(**entity.model_dump(by_alias=True))


@router.post("/{entity_id}", status_code=s.HTTP_200_OK)
@router.post("/{entitiy_id}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(
    entity_id: str,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> EntityDAO:
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    entity = entity_coll.find_one({"_id": entity_id})
    if not entity:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Entity with ID={entity_id} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    entity = EntityDAO.model_validate(entity)
    return entity


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
    external_id_key: Optional[str] = Query(None, alias="external_ids.key"),
    external_id_value: Optional[str] = Query(None, alias="external_ids.value"),
):
    orgs = reading.read_many(
        infostar=infostar,
        model=EntityDAO,
        **request.query_params,
    )
    return orgs


@router.post("/{entity_id}/roles", status_code=s.HTTP_201_CREATED)
@router.post("/{entity_id}/roles/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def add_entity_role(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    entity_id: str = PathParam(),
    role_id: Optional[PyObjectId] = Query(None),
    role_name: Optional[str] = Query(None),
):
    logger.debug(f"Adding role (role_id={role_id!r}, role_name={role_name!r}) to entity {entity_id!r}.")
    if not ((not role_id and role_name) or (role_id and not role_name)):
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail="Either role ID or name must be provided.",
        )

    # Check if entity exists
    logger.debug(f"Checking if entity {entity_id!r} exists.")
    entity = await read_one(
        entity_id=request.path_params["entity_id"],
        infostar=infostar,
    )

    # Create filters to find role
    # - Role's entity_ref.handle must be EITHER:
    #   - Equal to entity.handle
    #   - Partial match with base organization (inheritance)
    filters = {}
    if role_id:
        filters["_id"] = role_id
    elif role_name:
        filters["name"] = role_name
    if entity.owner_ref:
        logger.debug(f"Entity has owner_ref={entity.owner_ref!r}.")
        entity_root_org = f"/{entity.owner_ref.handle.split("/")[1]}"
        entity_root_org = re.escape(entity_root_org)
        logger.debug(f"Entity's root organization: {entity_root_org!r}.")
        filters["$or"] = [
            {"entity_ref.handle": entity.handle},
            {"entity_ref.handle": {"$regex": f"^{entity_root_org}"}},
        ]
    else:
        filters["entity_ref.handle"] = entity.handle
    logger.debug(f"Filters to find role: {filters!r}.")

    role = reading.read_one_filters(
        infostar=infostar,
        model=RoleDAO,
        **filters,
    )
    if not role:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail="Role not found.",
        )
    logger.debug(f"Role found: {role!r}.")
    # 409 in case the role is already attached
    for r in entity.roles:
        if r.id == role.id:
            raise HTTPException(
                status_code=s.HTTP_409_CONFLICT,
                detail=f"Role {role.name!r} already attached to entity {entity.handle!r}.",
            )
    # Add role to entity
    role_ref = RoleRef(id=role.id, entity=role.entity_ref)
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = entity_coll.update_one(
        {"_id": entity.id},
        {"$push": {"roles": role_ref.model_dump(mode="python")}},
    )
    logger.debug(f"Update result: {res!r}.")
    return {
        "msg": "Role added to entity.",
        "role_id": str(role.id),
        "entity_id": str(entity.id),
    }

@router.delete(
    "/{entity_id}/roles/{role_id}",
    status_code=s.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/{entity_id}/roles/{role_id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def remove_entity_role(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    entity_id: str = PathParam(),
    role_id: PyObjectId = PathParam(),
):
    logger.debug(f"Removing role {role_id!r} from entity {entity_id!r}.")
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = entity_coll.update_one(
        {"_id": entity_id},
        {"$pull": {"roles": {"id": role_id}}},
    )
    logger.debug(f"Update result: {res!r}.")
    return {
        "msg": "Role removed from entity.",
        "role_id": str(role_id),
        "entity_id": str(entity_id),
    }
