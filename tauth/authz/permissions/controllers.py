from collections.abc import Iterable

from redbaby.pyobjectid import PyObjectId

from ...settings import Settings
from ..roles.models import RoleDAO
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
                role_id=role_id,
            )
            for x in obj["permissions"]
        ]

    return return_dict


def get_permissions_set(roles: Iterable[PyObjectId]) -> set[PermissionContext]:
    permissions = read_permissions_from_roles(roles)
    return set(
        context for contexts in permissions.values() for context in contexts
    )
