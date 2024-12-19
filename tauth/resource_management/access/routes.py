from pathlib import Path

from fastapi import APIRouter, Depends
from loguru import logger

from tauth.authz.permissions.controllers import upsert_permission
from tauth.authz.permissions.schemas import PermissionIn
from tauth.dependencies.authentication import authenticate
from tauth.entities.routes import add_entity_permission
from tauth.entities.schemas import EntityRefIn
from tauth.utils import reading

from ...entities.models import EntityDAO
from ...schemas import Infostar
from ..resources.models import ResourceDAO
from .schemas import GrantIn, GrantResponse

service_name = Path(__file__).parents[1].name
router = APIRouter(prefix=f"/{service_name}/access", tags=[service_name])


@router.post("/$grant", status_code=201)
async def grant_access(
    body: GrantIn,
    infostar: Infostar = Depends(authenticate),
):
    resource = reading.read_one(
        infostar=infostar,
        model=ResourceDAO,
        identifier=body.resource_id,
    )

    entity = EntityDAO.from_handle_assert(
        body.entity_ref.handle, body.entity_ref.owner_handle
    )
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
        entity_id=entity.id, permission_id=p.id, infostar=infostar  # type: ignore
    )

    return GrantResponse(
        permission=body.permission_name, entity_id=str(entity.id)
    )
