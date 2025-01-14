from fastapi import HTTPException
from fastapi import status as s
from loguru import logger
from pymongo.errors import DuplicateKeyError

from tauth.entities.models import EntityDAO
from tauth.resource_management.resources.models import ResourceDAO
from tauth.schemas.infostar import Infostar
from tauth.settings import Settings
from tauth.utils import reading

from .schemas import ResourceIn


def create_one(
    body: ResourceIn,
    infostar: Infostar,
) -> ResourceDAO:
    service_entity = EntityDAO.from_handle(
        body.service_ref.handle, body.service_ref.owner_handle
    )
    if not service_entity:
        logger.error(f"Entity with handle {body.service_ref} not found")
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
    except DuplicateKeyError:
        raise HTTPException(
            status_code=s.HTTP_409_CONFLICT, detail="Resource already exists"
        )

    return item


def read_many(
    infostar: Infostar,
    service_handle: str | None,
    resource_collection: str | None,
    limit: int,
    offset: int,
) -> list[ResourceDAO]:
    filters = {}
    if service_handle:
        filters["service_ref.handle"] = service_handle
    if resource_collection:
        filters["resource_collection"] = resource_collection

    return reading.read_many(
        infostar=infostar,
        limit=limit,
        offset=offset,
        model=ResourceDAO,
        **filters,
    )
