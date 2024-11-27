from collections.abc import Iterable
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from tauth.authz.permissions.controllers import upsert_permission
from tauth.authz.permissions.schemas import PermissionIn
from tauth.dependencies.authentication import authenticate
from tauth.entities.routes import add_entity_permission
from tauth.entities.schemas import EntityRefIn
from tauth.schemas.gen_fields import GeneratedFields
from tauth.settings import Settings
from tauth.utils import reading

from ...entities.models import EntityDAO
from ...schemas import Infostar
from . import controllers
from .models import ResourceAccessDAO
from .schemas import GrantIn, ResourceAccessIn

service_name = Path(__file__).parents[1].name
router = APIRouter(prefix=f"/{service_name}/access", tags=[service_name])


@router.post("", status_code=s.HTTP_201_CREATED)
async def create_one(
    body: ResourceAccessIn = Body(),
    infostar: Infostar = Depends(authenticate),
) -> GeneratedFields:
    logger.debug(f"Creating Resource Access for: {body.entity_ref}")

    generated_fields, _ = controllers.create_one(body, infostar)
    return generated_fields


@router.get("/{access_id}", status_code=s.HTTP_200_OK)
async def read_one(
    access_id: PyObjectId,
    infostar: Infostar = Depends(authenticate),
):
    return reading.read_one(
        infostar=infostar, model=ResourceAccessDAO, identifier=access_id
    )


@router.get("", status_code=s.HTTP_200_OK)
async def read_many(
    infostar: Infostar = Depends(authenticate),
    resource_id: PyObjectId | None = Query(None),
    entity_ref: str | None = Query(None),
) -> Iterable[ResourceAccessDAO]:
    return controllers.read_many_access(
        infostar=infostar, resource_id=resource_id, entity_ref=entity_ref
    )


@router.delete("", status_code=s.HTTP_204_NO_CONTENT)
async def delete_one(
    access_id: PyObjectId,
    infostar: Infostar = Depends(authenticate),
):
    logger.debug(f"Deleting resource {access_id!r}")
    resource_coll = ResourceAccessDAO.collection(
        alias=Settings.get().REDBABY_ALIAS
    )
    resource_coll.delete_one({"_id": access_id})


@router.post("/$grant", status_code=201)
async def grant_access(
    body: GrantIn,
    infostar: Infostar = Depends(authenticate),
):
    try:
        created_access, resource = controllers.create_one(
            body=ResourceAccessIn(
                resource_id=body.resource_id, entity_ref=body.entity_ref
            ),
            infostar=infostar,
        )
        logger.debug(f"Created ResourceAccess: {created_access.id}")
    except HTTPException as e:
        if e.status_code == 409:
            logger.debug(
                f"Entity {body.entity_ref} already has ResourceAccess"
            )
            pass
        else:
            raise e

    entity = EntityDAO.from_handle(
        body.entity_ref.handle, body.entity_ref.owner_handle
    )
    assert entity
    permission_obj = PermissionIn(
        name=body.permission_name,
        description="Permission created for resource access, by tauth $grant",
        entity_ref=EntityRefIn(
            handle=resource.service_ref.handle,
            owner_handle=resource.service_ref.owner_handle,
        ),
        type="resource",
    )

    p = upsert_permission(permission_in=permission_obj, infostar=infostar)
    logger.debug(f"Upserted permission: {p.id}")

    # add permission to entity
    await add_entity_permission(
        entity_id=entity.id, permission_id=p.id, infostar=infostar
    )

    return {
        "msg": "Granted Access to entity with permission.",
        "permission": str(body.permission_name),
        "entity_id": str(entity.id),
    }
