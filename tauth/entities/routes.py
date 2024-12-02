from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi import Path as PathParam
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from tauth.authz.permissions.models import PermissionDAO
from tauth.dependencies.authentication import authenticate

from ..authz import privileges
from ..authz.roles.models import RoleDAO
from ..authz.roles.schemas import RoleRef
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..settings import Settings
from ..utils import creation, reading
from .models import EntityDAO, EntityIntermediate
from .schemas import EntityIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 👥💻🏢"])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    body: EntityIn = Body(openapi_examples=EntityIn.get_entity_examples()),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    if body.owner_ref:
        owner_ref = EntityDAO.from_handle_to_ref(
            body.owner_ref.handle,
            owner_handle=body.owner_ref.owner_handle,
        )
        if not owner_ref:
            d = {
                "error": "DocumentNotFound",
                "msg": "Owner not found.",
            }
            raise HTTPException(status_code=404, detail=d)
    else:
        owner_ref = None
    schema_in = EntityIntermediate(
        owner_ref=owner_ref,
        roles=list(map(lambda x: RoleRef(id=PyObjectId(x)), body.roles)),
        **body.model_dump(exclude={"owner_ref", "roles"}),
    )
    entity = creation.create_one(schema_in, EntityDAO, infostar)
    return GeneratedFields(**entity.model_dump(by_alias=True))


@router.post("/{entity_id}", status_code=s.HTTP_200_OK)
@router.post(
    "/{entitiy_id}/", status_code=s.HTTP_200_OK, include_in_schema=False
)
async def read_one(
    entity_id: str,
    infostar: Infostar = Depends(authenticate),
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
async def read_many(
    request: Request,
    infostar: Infostar = Depends(authenticate),
    name: str | None = Query(None),
    external_id_key: str | None = Query(None, alias="external_ids.key"),
    external_id_value: str | None = Query(None, alias="external_ids.value"),
):
    orgs = reading.read_many(
        infostar=infostar,
        model=EntityDAO,
        **request.query_params,
    )
    return orgs


@router.post("/{entity_id}/roles", status_code=s.HTTP_201_CREATED)
@router.post(
    "/{entity_id}/roles/",
    status_code=s.HTTP_201_CREATED,
    include_in_schema=False,
)
async def add_entity_role(
    request: Request,
    infostar: Infostar = Depends(authenticate),
    entity_id: str = PathParam(),
    role_id: PyObjectId | None = Query(None),
    role_name: str | None = Query(None),
):
    logger.debug(
        f"Adding role (role_id={role_id!r}, role_name={role_name!r}) to entity {entity_id!r}."
    )
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
    for role_ref in entity.roles:
        r = RoleDAO.from_ref(role_ref)
        assert r
        if r.name == role.name:
            raise HTTPException(
                status_code=s.HTTP_409_CONFLICT,
                detail=f"Role {role.name!r} already attached to entity {entity.handle!r}.",
            )
    # Add role to entity
    role_ref = RoleRef(id=role.id)
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = entity_coll.update_one(
        {"_id": entity.id},
        {"$push": {"roles": role_ref.model_dump(mode="python")}},
    )
    logger.debug(f"Update result: {res!r}.")
    return {
        "msg": "Role added to entity.",
        "role_name": str(role.name),
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
    infostar: Infostar = Depends(authenticate),
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


@router.post("/{entity_id}/permissions", status_code=s.HTTP_201_CREATED)
async def add_entity_permission(
    infostar: Infostar = Depends(authenticate),
    entity_id: str = PathParam(),
    permission_id: PyObjectId = Query(),
):
    logger.debug(f"Adding permission (permission_id={permission_id!r}")

    # Check if entity exists
    logger.debug(f"Checking if entity {entity_id!r} exists.")
    entity = await read_one(
        entity_id=entity_id,
        infostar=infostar,
    )

    permission = reading.read_one(
        infostar=infostar,
        model=PermissionDAO,
        identifier=permission_id,
    )

    logger.debug(f"permission found: {permission!r}.")
    # 409 in case the permission is already attached
    for p in entity.permissions:
        if p == permission.id:
            raise HTTPException(
                status_code=s.HTTP_409_CONFLICT,
                detail=f"Permission {permission.name!r} already attached to entity {entity.handle!r}.",
            )
    # Add permission to entity
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = entity_coll.update_one(
        {"_id": entity.id},
        {"$push": {"permissions": permission.id}},
    )
    logger.debug(f"Update result: {res!r}.")
    return {
        "msg": "Permission added to entity.",
        "permission_name": str(permission.name),
        "entity_id": str(entity.id),
    }


@router.delete(
    "/{entity_id}/permissions/{permission_id}",
    status_code=s.HTTP_204_NO_CONTENT,
)
async def remove_entity_permission(
    request: Request,
    infostar: Infostar = Depends(authenticate),
    entity_id: str = PathParam(),
    permission_id: PyObjectId = PathParam(),
):
    logger.debug(
        f"Removing permission {permission_id!r} from entity {entity_id!r}."
    )
    entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = entity_coll.update_one(
        {"_id": entity_id},
        {"$pull": {"permissions": permission_id}},
    )
    logger.debug(f"Update result: {res!r}.")
    return {
        "msg": "Permission removed from entity.",
        "permission_id": str(permission_id),
        "entity_id": str(entity_id),
    }
