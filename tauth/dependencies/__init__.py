from fastapi import FastAPI

from ..settings import Settings
from . import authentication, authorization, database


def init_app(app: FastAPI, sets: Settings) -> None:
    database.init_app(sets)
    authentication.init_app(app)
    authorization.setup_engine()
