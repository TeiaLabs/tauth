from collections.abc import Iterable

from redbaby.pyobjectid import PyObjectId

from tauth.settings import Settings

from ...schemas import Infostar
from .models import ResourceAccessDAO


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
