from fastapi import APIRouter, FastAPI

from . import client, tokens, users


def init_app(app: FastAPI) -> None:
    router = APIRouter(prefix="/api")
    router.include_router(get_router(None))
    app.include_router(router)


def get_router(prefix: str | None) -> APIRouter:
    if prefix is None:
        prefix = __name__.split(".")[-2]
    base_router = APIRouter(prefix=f"/{prefix}", tags=[prefix])
    base_router.include_router(client.router)
    base_router.include_router(tokens.router)
    base_router.include_router(users.router)
    return base_router
