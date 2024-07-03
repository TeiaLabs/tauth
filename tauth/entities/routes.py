from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi import status as s

from ..authz import privileges
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..utils import creation, reading
from .models import EntityDAO
from .schemas import EntityIn, EntityIntermediate

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 👥💻🏢"])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    body: EntityIn = Body(
        openapi_examples=EntityIn.model_config["json_schema_extra"]["examples"][0]
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    if body.owner_handle:
        owner_ref = EntityDAO.from_handle_to_ref(body.owner_handle)
    else:
        owner_ref = None
    schema_in = EntityIntermediate(owner_ref=owner_ref, **body.model_dump())
    entity = creation.create_one(schema_in, EntityDAO, infostar)
    return GeneratedFields(**entity.model_dump(by_alias=True))


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    name: Optional[str] = Query(None),
    external_id_key: Optional[str] = Query(None, alias="external_ids.key"),
    external_id_value: Optional[str] = Query(None, alias="external_ids.value"),
):
    orgs = reading.read_many(
        infostar=infostar,
        model=EntityDAO,
        **request.query_params,
    )
    return orgs
