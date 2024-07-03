from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi import status as s

from ..authz import privileges
from ..dependencies.security import RequestAuthenticator
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..utils import creation, reading
from .models import AuthorizationPolicyDAO
from .schemas import AuthorizationDataIn, AuthorizationPolicyIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🔐"])


# TODO: read_one, update_one, delete_one


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authorize(
    request: Request,
    body: AuthorizationDataIn = Body(),
    infostar: Infostar = Depends(RequestAuthenticator.validate),
) -> Any:
    body.context["infostar"] = infostar
    body.context["request"] = request
    policy = reading.read_many(
        infostar=infostar,
        model=AuthorizationPolicyDAO,
        **{"name": body.policy_name},
    )
    # TODO: execute using policy engine
    return True


@router.post("/policies", status_code=s.HTTP_201_CREATED)
@router.post("/policies/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    body: AuthorizationPolicyIn = Body(),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    policy = creation.create_one(body, AuthorizationPolicyDAO, infostar)
    return GeneratedFields(**policy.model_dump(by_alias=True))


@router.get("/policies", status_code=s.HTTP_200_OK)
@router.get("/policies/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
):
    policy = reading.read_many(
        infostar=infostar,
        model=AuthorizationPolicyDAO,
        **request.query_params,
    )
    return policy
