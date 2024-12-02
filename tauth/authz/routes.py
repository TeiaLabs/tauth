from pathlib import Path

from fastapi import APIRouter, Body, Request
from fastapi import status as s

from tauth.entities.models import EntityDAO
from tauth.schemas.infostar import Infostar

from . import controllers as authz_controllers
from .engines.interface import AuthorizationResponse
from .policies.schemas import AuthorizationDataIn
from .utils import get_allowed_permissions

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🔐"])


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authorize(
    request: Request,
    authz_data: AuthorizationDataIn = Body(),
) -> AuthorizationResponse:
    infostar: Infostar = request.state.infostar
    entity = EntityDAO.from_handle_assert(
        handle=infostar.user_handle,
        owner_handle=infostar.user_owner_handle,
    )
    allowed_permissions = get_allowed_permissions(request)

    result = await authz_controllers.authorize(
        request, entity, authz_data, allowed_permissions=allowed_permissions
    )
    return result
