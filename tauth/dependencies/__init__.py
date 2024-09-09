from fastapi import FastAPI

from ..settings import Settings
from . import authorization, database, security


def init_app(app: FastAPI, sets: Settings) -> None:
    database.init_app(sets)
    security.init_app(app)
    authorization.init_app()
