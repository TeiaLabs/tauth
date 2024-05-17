from importlib.metadata import version

from fastapi import APIRouter, FastAPI

from . import dependencies
from .authproviders import router as authproviders_router
from .entities import router as entities_router
from .legacy import client, tokens, users
from .settings import Settings


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title="TAuth",
        description="**T**eia **Auth**entication Service.",
        version=version("tauth"),
    )
    dependencies.init_app(app, settings)

    # Routes
    @app.get("/", status_code=200, tags=["health"])
    def _():
        return {"status": "ok"}

    router = APIRouter(prefix="/api")
    router.include_router(get_router(None))
    app.include_router(router)

    return app


def get_router(prefix: str | None) -> APIRouter:
    if prefix is None:
        prefix = __name__.split(".")[-2]
    base_router = APIRouter(prefix=f"/{prefix}")
    base_router.include_router(entities_router)
    base_router.include_router(authproviders_router)
    base_router.include_router(users.router)  # keep this first
    base_router.include_router(client.router)
    base_router.include_router(tokens.router)
    return base_router
