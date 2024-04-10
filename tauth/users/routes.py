from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi import status as s

from ..injections import privileges
from ..schemas import Creator
from ..utils import validate_creation_access_level
from . import controllers
from ..schemas.gen_fields import GeneratedFields

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    org_in: OrganizationIn = Body(),
    creator: Creator = Depends(privileges.is_valid_admin),
):
    validate_creation_access_level(org_in.name, creator.client_name)
    org = controllers.create_one(org_in, creator)
    return GeneratedFields(**org.model_dump(by_alias=True))


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    creator: Creator = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
    external_id_key: Optional[str] = Query(None, alias="external_ids.key"),
    external_id_value: Optional[str] = Query(None, alias="external_ids.value"),
):
    orgs = controllers.read_many(
        creator=creator,
        **request.query_params,
    )
    return orgs
