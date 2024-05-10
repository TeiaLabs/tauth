from redbaby.database import DB
from redbaby.document import Document

from ..settings import Settings


def init_app(sets: Settings):
    DB.add_conn(
        db_name=sets.TAUTH_MONGODB_DBNAME,
        uri=sets.TAUTH_MONGODB_URI,
        alias=Settings.get().TAUTH_REDBABY_ALIAS,
    )
    for m in Document.__subclasses__():
        m.create_indexes(alias=Settings.get().TAUTH_REDBABY_ALIAS)
