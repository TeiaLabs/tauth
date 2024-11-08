from pathlib import Path

from fastapi import APIRouter, Body, Request
from fastapi import status as s

from . import controllers as authz_controllers
from .engines.interface import AuthorizationResponse
from .policies.schemas import AuthorizationDataIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🔐"])


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authorize(
    request: Request,
    authz_data: AuthorizationDataIn = Body(),
) -> AuthorizationResponse:
    result = await authz_controllers.authorize(request, authz_data)
    return result
