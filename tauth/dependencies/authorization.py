from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi import status as s
from fastapi.security import HTTPAuthorizationCredentials

from tauth.authz import controllers as authz_controllers
from tauth.authz.policies.schemas import AuthorizationDataIn
from tauth.schemas.infostar import Infostar
from tauth.settings import Settings

from ..authz.engines.factory import AuthorizationEngine
from ..authz.engines.interface import AuthorizationResponse
from ..utils.headers import auth_headers_injector
from .authentication import authn


def setup_engine():
    AuthorizationEngine.setup()


def init_app(app: FastAPI, authz_data: AuthorizationDataIn):
    app.router.dependencies.append(Depends(authz(authz_data), use_cache=True))


def init_router(router: APIRouter, authz_data: AuthorizationDataIn):
    router.dependencies.append(Depends(authz(authz_data), use_cache=True))


def authz(authz_data: AuthorizationDataIn, _: Infostar = Depends(authn())):

    @auth_headers_injector
    async def _authorize(
        request: Request,
        background_tasks: BackgroundTasks,
        user_email: str | None = None,
        id_token: str | None = None,
        authorization: HTTPAuthorizationCredentials | None = None,
    ) -> AuthorizationResponse:
        if not authz_data:
            raise HTTPException(
                status_code=s.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid or missing authorization data.",
            )
        if Settings.get().AUTHN_ENGINE == "remote":
            engine = AuthorizationEngine.get()
            result = engine.is_authorized(
                policy_name=authz_data.policy_name,
                rule=authz_data.rule,
                context=authz_data.context,
                resources=authz_data.resources,
            )
        else:
            result = await authz_controllers.authorize(request, authz_data)

        if not result.authorized:
            raise HTTPException(
                status_code=s.HTTP_403_FORBIDDEN, detail=result.details
            )
        request.state.authz_result = result
        return result

    return _authorize
