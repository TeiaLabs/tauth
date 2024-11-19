from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import status as s
from loguru import logger
from pymongo.errors import DuplicateKeyError
from redbaby.pyobjectid import PyObjectId

from tauth.resource_management.access.models import ResourceAccessDAO

from ...authz import privileges
from ...entities.models import EntityDAO
from ...schemas import Infostar
from ...schemas.gen_fields import GeneratedFields
from ...settings import Settings
from ...utils import reading
from . import controllers
from .models import ResourceDAO
from .schemas import ResourceIn, ResourceUpdate

service_name = Path(__file__).parents[1].name
router = APIRouter(prefix=f"/{service_name}/resources", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    body: ResourceIn = Body(
        openapi_examples=ResourceIn.get_resource_in_examples()
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):

    service_entity = EntityDAO.from_handle(
        body.service_ref.handle, body.service_ref.owner_handle
    )
    if not service_entity:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=f"Entity with handle {body.service_ref} not found",
        )

    try:
        item = ResourceDAO(
            created_by=infostar,
            service_ref=service_entity.to_ref(),
            **body.model_dump(
                exclude={"entity_handle", "role_name", "service_ref"}
            ),
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
    resource_collection: str | None = Query(None),
) -> list[ResourceDAO]:
    logger.debug(f"Reading many Resources for {infostar.user_handle}")

    return controllers.read_many(
        infostar=infostar,
        service_handle=service_handle,
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
    resource = reading.read_one(
        infostar=infostar,
        model=ResourceDAO,
        identifier=resource_id,
    )
    return resource


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
    logger.debug(f"Trying to delete resource {resource_id!r}")
    alias = Settings.get().REDBABY_ALIAS

    resource_coll = ResourceDAO.collection(alias=alias)
    res = resource_coll.delete_one({"_id": resource_id})
    if res.deleted_count > 0:
        logger.info(
            f"Deleted resource {resource_id!r}, deleting related access"
        )
        access_coll = ResourceAccessDAO.collection(alias=alias)
        res = access_coll.delete_many({"resource_id": resource_id})
        logger.info(
            f"Deleted {res.deleted_count} access related to resource {resource_id!r}"
        )


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
