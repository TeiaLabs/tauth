from cachetools.func import lfu_cache
from fastapi import HTTPException

from ..schemas import Creator
from ..settings import Settings
from .models import OrganizationDAO
from .schemas import OrganizationIn


def create_one(item: OrganizationIn, creator: Creator) -> OrganizationDAO:
    client = OrganizationDAO(**item.dict(), created_by=creator)
    OrganizationDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).insert_one(client)
    return client


def read_many(creator: Creator, **filters) -> list[OrganizationDAO]:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = OrganizationDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_many(
        query
    )
    return objs  # type: ignore


# @lfu_cache(maxsize=128)
def read_one(external_id_key: str, external_id_value: str) -> OrganizationDAO:
    print(external_id_key, external_id_value)
    try:
        item = OrganizationDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_one(
            {
                "external_ids.name": external_id_key,
                "external_ids.value": external_id_value,
            }
        )
    except Exception:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Organization with {external_id_key}={external_id_value} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    return item  # type: ignore
