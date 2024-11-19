from collections.abc import Iterable

from tauth.entities.models import EntityDAO
from tauth.resource_management.access.models import ResourceAccessDAO
from tauth.resource_management.resources.models import ResourceDAO
from tauth.schemas.infostar import Infostar
from tauth.utils import reading

from .schemas import ResourceContext


def format_context(res: dict):
    resource_details = res["resource_details"]
    return ResourceContext(**resource_details)


def read_many(
    infostar: Infostar,
    service_handle: str | None,
    resource_collection: str | None,
) -> list[ResourceDAO]:
    filters = {}
    if service_handle:
        filters["service_ref.handle"] = service_handle
    if resource_collection:
        filters["resource_collection"] = resource_collection

    return reading.read_many(infostar=infostar, model=ResourceDAO, **filters)


def get_context_resources(
    entity: EntityDAO,
    service: EntityDAO,
    resource_collection: str,
) -> Iterable[ResourceContext]:
    """Get context resources

    Args:
        entity (EntityDAO): EntityDAO
        service_handle (str): service_handle
        resource_collection (str): resource_collection

    """
    entity_filters = {"entity_ref.handle": entity.handle}
    if entity.owner_ref:
        entity_filters["entity_ref.owner_handle"] = entity.owner_ref.handle

    resource_filters = {
        "resource_details.service_ref.handle": service.handle,
        "resource_details.resource_collection": resource_collection,
    }
    if service.owner_ref:
        resource_filters["resource_details.service_ref.owner_handle"] = (
            service.owner_ref.handle
        )

    pipeline = [
        {"$match": entity_filters},
        {
            "$lookup": {
                "from": "resources",
                "localField": "resource_id",
                "foreignField": "_id",
                "as": "resource_details",
            }
        },
        {"$unwind": "$resource_details"},
        {"$match": resource_filters},
    ]

    resources: Iterable[ResourceContext] = reading.aggregate(
        model=ResourceAccessDAO,
        pipeline=pipeline,
        formatter=format_context,
    )  # type: ignore

    return resources
