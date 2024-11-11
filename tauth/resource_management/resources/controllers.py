from tauth.entities.models import EntityDAO
from tauth.resource_management.access.models import ResourceAccessDAO
from tauth.resource_management.resources.models import ResourceDAO
from tauth.schemas.infostar import Infostar
from tauth.utils import reading

from .schemas import ResourceContext


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
    service_handle: str,
    resource_collection: str,
) -> list[ResourceContext]:
    """Get context resources

    Args:
        infostar (Infostar): Infostar
        entity (EntityDAO): EntityDAO
        service_handle (str): service_handle
        resource_collection (str): resource_collection

    """
    pipeline = [
        {"$match": {"entity_ref.handle": entity.handle}},
        {
            "$lookup": {
                "from": "resources",
                "localField": "resource_id",
                "foreignField": "_id",
                "as": "resource_details",
            }
        },
        {"$unwind": "$resource_details"},
        {
            "$match": {
                "resource_details.service_ref.handle": service_handle,
                "resource_details.resource_collection": resource_collection,
            }
        },
    ]

    resources = reading.aggregate(
        model=ResourceAccessDAO,
        result_model=ResourceDAO,
        pipeline=pipeline,
    )

    resource_context: list[ResourceContext] = []
    for resource in resources:
        obj = ResourceContext(
            service_ref=resource.service_ref,
            resource_collection=resource.resource_collection,
            ids=resource.ids,
            metadata=resource.metadata,
        )
        resource_context.append(obj)

    return resource_context
