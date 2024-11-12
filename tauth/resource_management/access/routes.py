from collections.abc import Iterable
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import status as s
from loguru import logger
from pymongo.errors import DuplicateKeyError
from redbaby.pyobjectid import PyObjectId

from tauth.resource_management.resources.models import ResourceDAO
from tauth.schemas.gen_fields import GeneratedFields
from tauth.settings import Settings
from tauth.utils import reading

from ...authz import privileges
from ...entities.models import EntityDAO
from ...schemas import Infostar
from . import controllers
from .models import ResourceAccessDAO
from .schemas import ResourceAccessIn

service_name = Path(__file__).parents[1].name
router = APIRouter(prefix=f"/{service_name}/access", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
async def create_one(
    body: ResourceAccessIn = Body(),
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> GeneratedFields:
    logger.debug(f"Creating Resource Access for: {body.entity_handle}")

    entity = EntityDAO.from_handle(body.entity_handle)

    if not entity:
        raise HTTPException(
            s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle"
        )

    resource = reading.read_one(
        infostar=infostar,
        model=ResourceDAO,
        identifier=body.resource_id,
    )

    resource_access = ResourceAccessDAO(
        created_by=infostar,
        resource_id=resource.id,
        entity_ref=entity.to_ref(),
    )
    try:
        ResourceAccessDAO.collection(
            alias=Settings.get().REDBABY_ALIAS
        ).insert_one(resource_access.bson())
    except DuplicateKeyError:
        m = f"Entity: {entity.handle} already has access to {resource.id!r}"
        raise HTTPException(
            status_code=s.HTTP_409_CONFLICT,
            detail=m,
        )

    return GeneratedFields(**resource_access.bson())


@router.get("/{access_id}", status_code=s.HTTP_200_OK)
async def read_one(
    access_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_user),
):
    return reading.read_one(
        infostar=infostar, model=ResourceAccessDAO, identifier=access_id
    )


@router.get("", status_code=s.HTTP_200_OK)
async def read_many(
    infostar: Infostar = Depends(privileges.is_valid_user),
    resource_id: PyObjectId | None = Query(None),
    entity_ref: str | None = Query(None),
) -> Iterable[ResourceAccessDAO]:
    return controllers.read_many_access(
        infostar=infostar, resource_id=resource_id, entity_ref=entity_ref
    )


@router.delete("", status_code=s.HTTP_204_NO_CONTENT)
async def delete_one(
    access_id: PyObjectId,
    infostar: Infostar = Depends(privileges.is_valid_user),
):
    logger.debug(f"Deleting resource {access_id!r}")
    resource_coll = ResourceAccessDAO.collection(
        alias=Settings.get().REDBABY_ALIAS
    )
    resource_coll.delete_one({"_id": access_id})
