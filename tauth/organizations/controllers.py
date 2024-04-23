from cachetools.func import lfu_cache
from fastapi import HTTPException
from pymongo import errors as pymongo_errors

from ..schemas import Creator
from ..settings import Settings
from .models import OrganizationDAO
from .schemas import OrganizationIn


def create_one(item: OrganizationIn, creator: Creator) -> OrganizationDAO:
    client = OrganizationDAO(**item.model_dump(), created_by=creator)
    try:
        res = OrganizationDAO.collection(
            alias=Settings.get().TAUTH_REDBABY_ALIAS
        ).insert_one(client.bson())
    except pymongo_errors.DuplicateKeyError as e:
        d = {
            "error": e.__class__.__name__,
            "msg": e._message,
            "details": e.details,
        }
        raise HTTPException(status_code=409, detail=d)
    return client


def read_many(creator: Creator, **filters) -> list:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = OrganizationDAO.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find(
        query
    )
    return objs


# @lfu_cache(maxsize=128)
def read_one(external_id_key: str, external_id_value: str):
    item = OrganizationDAO.collection(
        alias=Settings.get().TAUTH_REDBABY_ALIAS
    ).find_one(
        {
            "external_ids.name": external_id_key,
            "external_ids.value": external_id_value,
        }
    )
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Organization with {external_id_key}={external_id_value} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    return item
