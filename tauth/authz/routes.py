from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi import status as s
from loguru import logger

from ..authz.engines.factory import AuthorizationEngine
from ..dependencies.security import RequestAuthenticator
from ..entities.models import EntityDAO
from ..schemas import Infostar
from .policies.schemas import AuthorizationDataIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🔐"])


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authorize(
    request: Request,
    authz_data: AuthorizationDataIn = Body(),
) -> dict:
    infostar = request.state.infostar
    logger.debug(f"Running authorization for user: {infostar}")
    logger.debug(f"Authorization data: {authz_data}")

    logger.debug("Getting authorization engine and adding context.")
    authz_engine = AuthorizationEngine.get()
    authz_data.context["infostar"] = infostar.model_dump(mode="json")
    authz_data.context["request"] = await request.json()
    entity = EntityDAO.from_handle(handle=infostar.user_handle)
    if not entity:
        message = f"Entity not found for handle: {infostar.user_handle}."
        logger.error(message)
        raise HTTPException(
            status_code=s.HTTP_401_UNAUTHORIZED,
            detail=dict(msg=message),
        )
    logger.debug(f"Entity found: {entity}.")

    logger.debug(f"Executing authorization logic.")
    # TODO: determine if we're gonna support arbitrary outputs here (e.g., filters)
    result = authz_engine.is_authorized(
        entity=entity,
        policy_name=authz_data.policy_name,
        resource=authz_data.resource,
        context=authz_data.context,
    )
    logger.debug(f"Authorization result: {result}.")
    result = dict(authorized=result)
    return result
