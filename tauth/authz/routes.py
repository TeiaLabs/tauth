from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Request
from fastapi import status as s

from ..authz.engines.factory import AuthorizationEngine
from ..dependencies.security import RequestAuthenticator
from ..schemas import Infostar
from ..utils import reading
from .policies.models import AuthorizationPolicyDAO
from .policies.schemas import AuthorizationDataIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🔐"])


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authorize(
    request: Request,
    authz_data: AuthorizationDataIn = Body(),
    infostar: Infostar = Depends(RequestAuthenticator.validate),
) -> Any:
    authz_engine = AuthorizationEngine.get()

    authz_data.context["infostar"] = infostar.model_dump(mode="json")
    authz_data.context["request"] = request

    result = authz_engine.is_authorized(
        entity=None,
        policy_name=authz_data.policy_name,
        context=authz_data.context,
    )
    return result
