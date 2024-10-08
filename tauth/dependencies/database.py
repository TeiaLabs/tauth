from redbaby.database import DB
from redbaby.document import Document

from ..settings import Settings


def setup_database(dbname: str, dburi: str, redbaby_alias: str):
    DB.add_conn(
        db_name=dbname,
        uri=dburi,
        alias=redbaby_alias,
    )
    for m in Document.__subclasses__():
        if m.__module__.startswith("tauth"):
            m.create_indexes(alias=redbaby_alias)


def init_app(sets: Settings):
    setup_database(
        dbname=sets.MONGODB_DBNAME,
        dburi=sets.MONGODB_URI,
        redbaby_alias=sets.REDBABY_ALIAS,
    )
