from redbaby.database import DB
from redbaby.document import Document

from ..models import all_models
from ..settings import Settings


def init_app(sets: Settings):
    DB.add_conn(
        db_name=sets.TAUTH_MONGODB_DBNAME,
        uri=sets.TAUTH_MONGODB_URI,
        alias="tauth",
    )
    for m in Document.__subclasses__():
        m.create_indexes(alias="tauth")
