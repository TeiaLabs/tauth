from collections.abc import Iterable

from fastapi import HTTPException
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from tauth.entities.models import EntityDAO
from tauth.entities.schemas import EntityRef
from tauth.schemas.gen_fields import GeneratedFields
from tauth.schemas.infostar import Infostar

from ...settings import Settings
from ..roles.models import RoleDAO
from .models import PermissionDAO, PermissionType
from .schemas import PermissionContext, PermissionIn, PermissionIntermediate


def read_permissions_from_roles(
    roles: Iterable[PyObjectId],
) -> dict[PyObjectId, list[PermissionContext]]:

    pipeline = [
        {"$match": {"_id": {"$in": list(roles)}}},
        {
            "$lookup": {
                "from": "authz-permissions",
                "localField": "permissions",
                "foreignField": "_id",
                "as": "permissions_info",
            }
        },
        {
            "$unwind": {
                "path": "$permissions_info",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "permissions": {"$addToSet": "$permissions_info"},
            }
        },
    ]

    role_coll = RoleDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    res = role_coll.aggregate(pipeline)

    return_dict = {}
    for obj in res:
        role_id = obj["_id"]
        return_dict[role_id] = [
            PermissionContext(
                name=x["name"],
                entity_handle=x["entity_ref"]["handle"],
            )
            for x in obj["permissions"]
        ]

    return return_dict


def read_many_permissions(
    perms: list[PyObjectId],
    type: PermissionType | None = None,
    entity_ref: EntityRef | None = None,
) -> set[PermissionContext]:

    permission_coll = PermissionDAO.collection(
        alias=Settings.get().REDBABY_ALIAS
    )
    filters: dict = {"_id": {"$in": perms}}
    if type:
        filters["type"] = type
    if entity_ref:
        filters["entity_ref.handle"] = entity_ref.handle
        if entity_ref.owner_handle:
            filters["entity_ref.owner_handle"] = entity_ref.owner_handle

    permissions = permission_coll.find(filters)

    s = set()
    for p in permissions:
        s.add(
            PermissionContext(
                name=p["name"],
                entity_handle=p["entity_ref"]["handle"],
            )
        )

    return s


def upsert_permission(permission_in: PermissionIn, infostar: Infostar):
    entity_ref = EntityDAO.from_handle_to_ref(
        permission_in.entity_ref.handle,
        owner_handle=permission_in.entity_ref.owner_handle,
    )

    if not entity_ref:
        raise HTTPException(
            s.HTTP_400_BAD_REQUEST, detail="Invalid entity handle"
        )
    schema_in = PermissionIntermediate(
        entity_ref=entity_ref,
        **permission_in.model_dump(exclude={"entity_ref"}),
    )
    model = PermissionDAO(**schema_in.model_dump(), created_by=infostar)

    coll = PermissionDAO.collection(alias=Settings.get().REDBABY_ALIAS)
    permission = coll.find_one(
        {"name": model.name, "entity_ref.handle": model.entity_ref.handle}
    )
    if permission:
        obj = PermissionDAO(**permission)
        return GeneratedFields(
            _id=obj.id,
            created_at=obj.created_at,
            created_by=obj.created_by,
        )

    res = coll.insert_one(
        model.bson(),
    )
    logger.debug(f"Upserted permission res: {res}")

    return GeneratedFields(**model.model_dump(by_alias=True))
