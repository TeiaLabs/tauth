from importlib.metadata import version

from fastapi import APIRouter, FastAPI

from . import dependencies
from .authn.routes import router as authentication_router
from .authproviders import router as authproviders_router
from .authz.policies.routes import router as policy_router
from .authz.routes import router as authorization_router
from .entities import router as entities_router
from .legacy import client, tokens
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
    @app.get("/", status_code=200, tags=["health 🩺"])
    def _():
        return {"status": "ok"}

    router = APIRouter()
    router.include_router(get_router())
    app.include_router(router)

    return app


def get_router() -> APIRouter:
    base_router = APIRouter()
    base_router.include_router(authentication_router)
    base_router.include_router(authorization_router)
    base_router.include_router(policy_router)
    base_router.include_router(entities_router)
    base_router.include_router(authproviders_router)
    base_router.include_router(client.router)
    base_router.include_router(tokens.router)
    return base_router
