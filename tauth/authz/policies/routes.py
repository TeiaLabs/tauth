from pathlib import Path

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi import status as s
from loguru import logger

from ...authz import privileges
from ...schemas import Infostar
from ...schemas.gen_fields import GeneratedFields
from ...utils import reading
from ..policies.models import AuthorizationPolicyDAO
from ..policies.schemas import AuthorizationPolicyIn
from . import controllers as authz_controller
from .schemas import POLICY_EXAMPLES

service_name = Path(__file__).parents[1].name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🔐"])


@router.put("/policies", status_code=s.HTTP_201_CREATED)
@router.put("/policies/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def upsert_one(
    request: Request,
    body: AuthorizationPolicyIn = Body(openapi_examples=POLICY_EXAMPLES),
    infostar: Infostar = Depends(privileges.is_valid_admin),
) -> GeneratedFields:
    result = authz_controller.upsert_one(body, infostar)
    return result


@router.get("/policies/{id}", status_code=s.HTTP_200_OK)
@router.get("/policies/{id}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(
    request: Request,
    id: str,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> AuthorizationPolicyDAO:
    result = authz_controller.read_one(id)
    return result


@router.get("/policies", status_code=s.HTTP_200_OK)
@router.get("/policies/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> list[AuthorizationPolicyDAO]:
    filters: dict = {k: v for k, v in request.query_params.items() if v is not None}
    result = authz_controller.read_many(filters, infostar)
    return result


@router.delete("/policies/{id}", status_code=s.HTTP_204_NO_CONTENT)
@router.delete(
    "/policies/{id}/",
    status_code=s.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
async def delete_one(
    request: Request,
    id: str,
    infostar: Infostar = Depends(privileges.is_valid_admin),
) -> None:
    result = authz_controller.delete_one(id)
    return result
