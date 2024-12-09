from importlib.metadata import version

from fastapi import APIRouter, FastAPI

from tauth import dependencies

from .authn.routes import router as authentication_router
from .authproviders.routes import router as authproviders_router
from .authz.permissions.routes import router as permissions_router
from .authz.policies.routes import router as policy_router
from .authz.roles.routes import router as roles_router
from .authz.routes import router as authorization_router
from .entities.routes import router as entities_router
from .legacy import client, tokens
from .resource_management.access.routes import router as resource_access_router
from .resource_management.resources import router as resources_router
from .settings import Settings
from .tauth_keys.routes import router as token_router


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title="TAuth",
        description="**T**eia **Auth**entication Service.",
        version=version("tauth"),
    )

    # Routes
    @app.get("/", status_code=200, tags=["health 🩺"])
    def _():
        return {"status": "ok"}

    dependencies.init_app(app, settings)

    router = APIRouter()
    router.include_router(get_router())
    app.include_router(router)

    return app


def get_router() -> APIRouter:
    base_router = APIRouter()
    base_router.include_router(authentication_router)
    base_router.include_router(authorization_router)
    base_router.include_router(permissions_router)
    base_router.include_router(roles_router)
    base_router.include_router(policy_router)
    base_router.include_router(entities_router)
    base_router.include_router(authproviders_router)
    base_router.include_router(resources_router)
    base_router.include_router(client.router)
    base_router.include_router(tokens.router)
    base_router.include_router(resource_access_router)
    base_router.include_router(token_router)
    return base_router
