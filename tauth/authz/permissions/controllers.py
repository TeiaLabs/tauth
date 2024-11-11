from collections.abc import Iterable

from redbaby.pyobjectid import PyObjectId

from ...settings import Settings
from ..roles.models import RoleDAO
from .models import PermissionDAO
from .schemas import PermissionContext


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
) -> set[PermissionContext]:

    permission_coll = PermissionDAO.collection(
        alias=Settings.get().REDBABY_ALIAS
    )
    permissions = permission_coll.find({"_id": {"$in": perms}})

    s = set()
    for p in permissions:
        s.add(
            PermissionContext(
                name=p["name"],
                entity_handle=p["entity_ref"]["handle"],
            )
        )

    return s
