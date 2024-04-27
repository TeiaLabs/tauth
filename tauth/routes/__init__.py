from fastapi import APIRouter, FastAPI

from ..authproviders import router as authproviders_router
from ..entities import router as entities_router
from . import client, tokens, users


def init_app(app: FastAPI) -> None:
    router = APIRouter(prefix="/api")
    router.include_router(get_router(None))

    @app.get("/", status_code=200, tags=["health"])
    def _():
        return {"status": "ok"}

    app.include_router(router)


def get_router(prefix: str | None) -> APIRouter:
    if prefix is None:
        prefix = __name__.split(".")[-2]
    base_router = APIRouter(prefix=f"/{prefix}")
    base_router.include_router(entities_router)
    base_router.include_router(authproviders_router)
    base_router.include_router(client.router)
    base_router.include_router(tokens.router)
    base_router.include_router(users.router)
    return base_router
