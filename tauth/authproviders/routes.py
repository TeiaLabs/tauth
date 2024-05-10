from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi import status as s

from ..auth.melt_key.authorization import validate_creation_access_level
from ..entities.models import EntityDAO
from ..injections import privileges
from ..schemas import Creator
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
        openapi_examples=AuthProviderIn.model_config["json_schema_extra"]["examples"][0]
    ),
    creator: Creator = Depends(privileges.is_valid_admin),
):
    # validate_creation_access_level(org_in.name, creator.client_name)  # TODO implement this
    if body.service_name:
        service_ref = EntityDAO.from_handle_to_ref(body.service_name)
    else:
        service_ref = None
    org_ref = EntityDAO.from_handle_to_ref(body.organization_name)
    if org_ref is None:
        raise ValueError(f"Organization {body.organization_name} not found.")
    in_schema = AuthProviderMoreIn(
        **body.model_dump(),
        service_ref=service_ref,
        organization_ref=org_ref.model_dump(),
    )
    org = creation.create_one(in_schema, AuthProviderDAO, creator)
    return GeneratedFields(**org.model_dump(by_alias=True))


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    creator: Creator = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
):
    orgs = reading.read_many(
        creator=creator,
        model=AuthProviderDAO,
        **request.query_params,
    )
    return orgs
