from fastapi import HTTPException, Request
from fastapi import status as s
from loguru import logger

from tauth.authz.engines.errors import PolicyNotFound, RuleNotFound
from tauth.authz.engines.interface import AuthorizationResponse
from tauth.authz.permissions.schemas import PermissionContext

from ..authz.engines.factory import AuthorizationEngine
from ..entities.models import EntityDAO
from ..resource_management.resources.controllers import get_context_resources
from ..utils.errors import EngineException
from .policies.schemas import AuthorizationDataIn
from .utils import (
    get_permissions_set,
    get_request_context,
    read_many_permissions,
)


async def authorize(
    request: Request,
    entity: EntityDAO,
    authz_data: AuthorizationDataIn,
    allowed_permissions: set[PermissionContext] | None,
) -> AuthorizationResponse:
    logger.debug(f"Running authorization for entity: {entity.handle}")
    logger.debug(f"Authorization data: {authz_data}")

    logger.debug("Getting authorization engine and adding context.")
    authz_engine = AuthorizationEngine.get()

    authz_data.context["tauth_request"] = await get_request_context(request)

    authz_data.context["entity"] = entity.model_dump(mode="json")
    role_ids = map(lambda x: x.id, entity.roles)
    permissions = get_permissions_set(role_ids, entity.permissions)
    if allowed_permissions:
        permissions = permissions.intersection(allowed_permissions)

    authz_data.context["permissions"] = [
        permission.model_dump(mode="json") for permission in permissions
    ]

    if authz_data.resources:
        logger.debug(
            f"Getting resources for service: {authz_data.resources.service_ref.handle}."
        )
        service = EntityDAO.from_handle(
            handle=authz_data.resources.service_ref.handle,
            owner_handle=authz_data.resources.service_ref.owner_handle,
        )
        if not service:
            message = f"Entity not found for handle: {authz_data.resources.service_ref.handle}."
            logger.error(message)
            raise HTTPException(
                status_code=s.HTTP_401_UNAUTHORIZED,
                detail=dict(msg=message),
            )
        resource_permissions = read_many_permissions(
            entity.permissions, "resource", entity_ref=service.to_ref()
        )
        permissions = permissions.union(resource_permissions)
        resources = get_context_resources(
            entity=entity,
            service=service,
            resource_collection=authz_data.resources.resource_collection,
        )
        authz_data.context["resources"] = [
            resource.model_dump(mode="json", by_alias=True)
            for resource in resources
        ]

    authz_data.context["permissions"] = [
        permission.model_dump(mode="json") for permission in permissions
    ]
    logger.debug("Executing authorization logic.")
    # TODO: determine if we're gonna support arbitrary outputs here (e.g., filters)
    try:
        result = authz_engine.is_authorized(
            policy_name=authz_data.policy_name,
            rule=authz_data.rule,
            context=authz_data.context,
        )
    except EngineException as e:
        handle_errors(e)

    logger.debug(f"Authorization result: {result}.")
    return result


def handle_errors(e: EngineException):
    if isinstance(e, (PolicyNotFound | RuleNotFound)):
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=dict(msg=str(e)),
        )
    logger.error(f"Unhandled engine error: {str(e)}")
    raise HTTPException(
        status_code=s.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=dict(msg=f"Unhandled engine error: {str(e)}"),
    )
