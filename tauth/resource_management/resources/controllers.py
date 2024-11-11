from tauth.resource_management.resources.models import ResourceDAO
from tauth.schemas.infostar import Infostar
from tauth.utils import reading

from ...authz.permissions.controllers import read_permissions_from_roles
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


def get_context_resources(entity) -> list[ResourceContext]:
    resources = read_many(
        infostar=infostar,
        service_handle=service_handle,
        resource_collection=resource_collection,
    )

    permissions = read_permissions_from_roles(roles)

    resource_context: list[ResourceContext] = []
    for resource in resources:
        obj = ResourceContext(
            service_ref=resource.service_ref,
            resource_collection=resource.resource_collection,
            ids=resource.ids,
            metadata=resource.metadata,
            permissions=permissions[resource.role_ref.id],
        )
        resource_context.append(obj)

    return resource_context
