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
