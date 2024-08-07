from pathlib import Path
from typing import Optional, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi import status as s

from ..authz import privileges
from ..entities.models import EntityDAO, OrganizationRef, ServiceRef
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..utils import creation, reading
from .models import AuthProviderDAO
from .schemas import AuthProviderIn, AuthProviderMoreIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    body: AuthProviderIn = Body(
        openapi_examples=AuthProviderIn.model_config["json_schema_extra"]["examples"][0]  # type: ignore
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    if body.service_name:
        service_ref = EntityDAO.from_handle_to_ref(body.service_name)
        if not service_ref:
            raise HTTPException(
                status_code=s.HTTP_404_NOT_FOUND,
                detail=f"Provided service name {body.service_name!r} not found.",
            )
        service_ref = cast(ServiceRef, service_ref)
        service_ref = ServiceRef(**service_ref.model_dump())
    else:
        service_ref = None
    org_ref = EntityDAO.from_handle_to_ref(body.organization_name)
    if org_ref is None:
        raise ValueError(f"Organization {body.organization_name} not found.")
    org_ref = OrganizationRef(**org_ref.model_dump())
    in_schema = AuthProviderMoreIn(
        **body.model_dump(),
        service_ref=service_ref,
        organization_ref=org_ref,
    )
    org = creation.create_one(in_schema, AuthProviderDAO, infostar)
    return GeneratedFields(**org.model_dump(by_alias=True))


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
):
    orgs = reading.read_many(
        infostar=infostar,
        model=AuthProviderDAO,
        **request.query_params,
    )
    return orgs
