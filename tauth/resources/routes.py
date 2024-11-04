from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import status as s
from loguru import logger
from pymongo.errors import DuplicateKeyError
from redbaby.pyobjectid import PyObjectId

from ..authz import privileges
from ..authz.roles.models import RoleDAO
from ..authz.roles.schemas import RoleRef
from ..entities.models import EntityDAO
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..settings import Settings
from ..utils import reading
from . import controllers
from .models import ResourceDAO
from .schemas import ResourceIn, ResourceUpdate

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    body: ResourceIn = Body(
        openapi_examples=ResourceIn.model_config["json_schema_extra"]["examples"][0]  # type: ignore
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    """
    Your entity handle needs to be the owner of the role you want
    """
    role_owner_entity = EntityDAO.from_handle(body.entity_handle)
    if not role_owner_entity:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=f"Entity with handle {body.entity_handle} not found",
        )
    role = RoleDAO.from_name(
        name=body.role_name, entity_handle=role_owner_entity.handle
    )
    if not role:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=f"Role with name {body.role_name} not found",
        )
    service_entity = EntityDAO.from_handle(body.service_handle)
    if not service_entity:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=f"Entity with handle {body.service_handle} not found",
        )

    try:
        role_ref = RoleRef(id=role.id)
        item = ResourceDAO(
            role_ref=role_ref,
            created_by=infostar,
            service_ref=service_entity.to_ref(),
            **body.model_dump(exclude={"entity_handle", "role_name"}),
        )
        ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS).insert_one(
            item.bson()
        )
        doc = item.bson()
    except DuplicateKeyError:
        raise HTTPException(
            status_code=s.HTTP_409_CONFLICT, detail="Resource already exists"
        )

    return GeneratedFields(**doc)


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    infostar: Infostar = Depends(privileges.is_valid_user),
    service_handle: str | None = Query(None),
    role_ids: list[str] | None = Query(None),
    resource_collection: str | None = Query(None),
) -> list[ResourceDAO]:
    logger.debug(f"Reading many Resources for {infostar.user_handle}")

    return controllers.read_many(
        infostar=infostar,
        service_handle=service_handle,
        role_ids=(
            list(map(lambda x: PyObjectId(x), role_ids)) if role_ids else None
        ),
        resource_collection=resource_collection,
    )


@router.get("/{resource_id}", status_code=s.HTTP_200_OK)
@router.get(
    "/{resource_id}/", status_code=s.HTTP_200_OK, include_in_schema=False
)
async def read_one(
    resource_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_user),
):
    logger.debug(f"Reading resource {resource_id!r}.")
    role = reading.read_one(
        infostar=infostar,
        model=ResourceDAO,
        identifier=resource_id,
    )
    return role


@router.delete("/{resource_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.delete(
    "/{resource_id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def delete_one(
    resource_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    logger.debug(f"Deleting resource {resource_id!r}")
    resource_coll = ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    resource_coll.delete_one({"_id": resource_id})


@router.patch("/{resource_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.patch(
    "/{resource_id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def update_one(
    resource_id: PyObjectId,
    body: ResourceUpdate = Body(),
    infostar: Infostar = Depends(privileges.is_valid_user),
):
    reading.read_one(
        infostar=infostar,
        model=ResourceDAO,
        identifier=resource_id,
    )
    update = {}
    if body.append_ids:
        append_ids = [obj.model_dump() for obj in body.append_ids]
        update["$push"] = {"ids": {"$each": append_ids}}
    if body.remove_ids:
        update["$pull"] = {"ids": {"id": {"$in": body.remove_ids}}}
    if body.metadata:
        update["$set"] = {"metadata": body.metadata}

    logger.debug(f"Updating resource {resource_id!r}: {update}")

    resource_coll = ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    if body.append_ids and body.remove_ids:
        # Mongo does not allow pushing and pulling
        # from the same array at the same time
        part_update = {"$push": update.pop("$push")}
        resource_coll.update_one({"_id": resource_id}, part_update)

    resource_coll.update_one({"_id": resource_id}, update)
