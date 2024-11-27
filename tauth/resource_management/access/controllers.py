from collections.abc import Iterable

from fastapi import HTTPException
from fastapi import status as s
from pymongo.errors import DuplicateKeyError
from redbaby.pyobjectid import PyObjectId

from tauth.schemas.gen_fields import GeneratedFields
from tauth.settings import Settings
from tauth.utils import reading

from ...entities.models import EntityDAO
from ...schemas import Infostar
from ..resources.models import ResourceDAO
from .models import ResourceAccessDAO
from .schemas import ResourceAccessIn


def read_many_access(
    infostar: Infostar, resource_id: PyObjectId | None, entity_ref: str | None
) -> Iterable[ResourceAccessDAO]:
    filters = {}
    if resource_id:
        filters["resource_id"] = resource_id
    if entity_ref:
        filters["entity_ref.handle"] = entity_ref

    coll = ResourceAccessDAO.collection(alias=Settings.get().REDBABY_ALIAS)

    cursor = coll.find(**filters)

    return map(lambda x: ResourceAccessDAO(**x), cursor)


def create_one(
    body: ResourceAccessIn, infostar: Infostar
) -> tuple[GeneratedFields, ResourceDAO]:
    entity = EntityDAO.from_handle(
        body.entity_ref.handle, body.entity_ref.owner_handle
    )

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

    return GeneratedFields(**resource_access.bson()), resource
