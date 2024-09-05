from tauth.utils.fastapi_extension import setup_database

from ..settings import Settings


def init_app(sets: Settings):
    setup_database(
        dbname=sets.MONGODB_DBNAME,
        dburi=sets.MONGODB_URI,
        redbaby_alias=sets.REDBABY_ALIAS,
    )
