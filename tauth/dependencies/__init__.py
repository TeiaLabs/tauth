from fastapi import FastAPI

from ..settings import Settings
from . import cache, database, security


def init_app(app: FastAPI, sets: Settings) -> None:
    cache.init_app()
    database.init_app(sets)
    security.init_app(app)
