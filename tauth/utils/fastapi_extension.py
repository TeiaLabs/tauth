from fastapi import Depends
from redbaby.database import DB
from redbaby.document import Document

from tauth.dependencies.security import RequestAuthenticator


def setup_database(dbname: str, dburi: str, redbaby_alias: str):
    DB.add_conn(
        db_name=dbname,
        uri=dburi,
        alias=redbaby_alias,
    )
    for m in Document.__subclasses__():
        if m.__module__.startswith("tauth"):
            m.create_indexes(alias=redbaby_alias)


def get_depends():
    return Depends(RequestAuthenticator.validate)
