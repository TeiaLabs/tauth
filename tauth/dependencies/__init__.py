from fastapi import FastAPI

from ..settings import Settings
from . import database, security


def init_app(app: FastAPI, sets: Settings) -> None:
    database.init_app(sets)
    security.init_app(app)
    # ad_auth.init_app(app)
