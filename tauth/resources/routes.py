from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi import status as s
from pymongo.errors import DuplicateKeyError

from ..authz import privileges
from ..authz.roles.schemas import RoleRef
from ..entities.models import EntityDAO
from ..schemas import Infostar
from ..schemas.gen_fields import GeneratedFields
from ..settings import Settings
from .models import ResourceDAO
from .schemas import ResourceIn

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    body: ResourceIn = Body(
        openapi_examples=ResourceIn.model_config["json_schema_extra"]["examples"][0]  # type: ignore
    ),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    owner_entity = EntityDAO.from_handle(body.entity_handle)
    if not owner_entity:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=f"Entity with handle {body.entity_handle} not found",
        )
    try:
        role_ref = RoleRef(
            name=body.role_name,
            entity_ref=owner_entity.to_ref(),
        )
        item = ResourceDAO(
            role_ref=role_ref,
            created_by=infostar,
            **body.model_dump(exclude={"entity_handle", "role_name"}),
        )
        ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS).insert_one(
            item.bson()
        )
    except DuplicateKeyError:
        r = ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS).update_one(
            {
                "servide_ref.handle": body.service_handle,
                "role_ref.name": body.role_name,
                "resource_collection": body.resource_collection,
            },
            {"$push": {"ids": {"$each": body.ids}}},
        )
        if not r.modified_count:
            raise HTTPException(
                status_code=s.HTTP_409_CONFLICT,
                detail=f"Resource with service {body.service_handle} and role {body.role_name} already exists",
            )
        doc = ResourceDAO.collection(alias=Settings.get().REDBABY_ALIAS).find_one(
            {
                "servide_ref.handle": body.service_handle,
                "role_ref.name": body.role_name,
                "resource_collection": body.resource_collection,
            },
        )
        if not doc:
            raise HTTPException(
                status_code=s.HTTP_404_NOT_FOUND,
                detail=f"Resource with service {body.service_handle} and role {body.role_name} not found",
            )

        item = ResourceDAO(**doc)

    return GeneratedFields(**doc)


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(
    request: Request,
    infostar: Infostar = Depends(privileges.is_valid_user),
    service_handle: str | None = Query(None),
    role_name: str | None = Query(None),
):
    pass
