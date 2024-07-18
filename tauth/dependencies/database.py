from tauth.utils.fastapi_extension import setup_database

from ..settings import Settings


def init_app(sets: Settings):
    setup_database(
        dbname=sets.TAUTH_MONGODB_DBNAME,
        dburi=sets.TAUTH_MONGODB_URI,
        redbaby_alias=sets.TAUTH_REDBABY_ALIAS,
    )
