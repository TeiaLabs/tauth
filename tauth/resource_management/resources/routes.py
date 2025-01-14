from pathlib import Path

from fastapi import APIRouter, Body, Depends, Query
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from tauth.dependencies.authentication import authenticate

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
    infostar: Infostar = Depends(authenticate),
) -> GeneratedFields:

    item = controllers.create_one(body, infostar)

    return GeneratedFields(**item.model_dump(by_alias=True))


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    infostar: Infostar = Depends(authenticate),
    service_handle: str | None = Query(None),
    resource_collection: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(1024, gt=0, le=1024),
) -> list[ResourceDAO]:
    logger.debug(f"Reading many Resources for {infostar.user_handle}")

    return controllers.read_many(
        infostar=infostar,
        service_handle=service_handle,
        resource_collection=resource_collection,
        limit=limit,
        offset=offset,
    )


@router.get("/{resource_id}", status_code=s.HTTP_200_OK)
@router.get(
    "/{resource_id}/", status_code=s.HTTP_200_OK, include_in_schema=False
)
async def read_one(
    resource_id: PyObjectId,
    infostar: Infostar = Depends(authenticate),
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
    infostar: Infostar = Depends(authenticate),
):
    logger.debug(f"Trying to delete resource {resource_id!r}")
    alias = Settings.get().REDBABY_ALIAS

    resource_coll = ResourceDAO.collection(alias=alias)
    res = resource_coll.delete_one({"_id": resource_id})
    logger.debug(f"Deleted {res.deleted_count} resources.")


@router.patch("/{resource_id}", status_code=s.HTTP_204_NO_CONTENT)
@router.patch(
    "/{resource_id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def update_one(
    resource_id: PyObjectId,
    body: ResourceUpdate = Body(),
    infostar: Infostar = Depends(authenticate),
):
    reading.read_one(
        infostar=infostar,
        model=ResourceDAO,
        identifier=resource_id,
    )
    update = {}

    update["$set"] = {"metadata": body.metadata}

    logger.debug(f"Updating resource {resource_id!r}: {update}")

    resource_coll = ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS)

    resource_coll.update_one({"_id": resource_id}, update)
