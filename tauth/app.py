from importlib.metadata import version

from fastapi import FastAPI

from . import dependencies, routes
from .settings import Settings


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title="TAuth",
        description="**T**eia **Auth**entication Service.",
        version=version("tauth"),
    )
    dependencies.init_app(app, settings)
    routes.init_app(app)
    return app
