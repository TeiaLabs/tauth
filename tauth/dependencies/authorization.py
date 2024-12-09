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
from tauth.authz.engines.remote.engine import RemoteEngine
from tauth.authz.policies.schemas import AuthorizationDataIn
from tauth.authz.utils import get_allowed_permissions, get_request_context
from tauth.entities.models import EntityDAO
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


def authz(
    authz_data: AuthorizationDataIn, infostar: Infostar = Depends(authn())
):
    @auth_headers_injector
    async def _authorize(
        request: Request,
        background_tasks: BackgroundTasks,
        user_email: str | None = None,
        authorization: HTTPAuthorizationCredentials | None = None,
        impersonate_entity_handle: str | None = None,
        impersonate_entity_owner: str | None = None,
    ) -> AuthorizationResponse:
        if not authz_data:
            raise HTTPException(
                status_code=s.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid or missing authorization data.",
            )
        authz_data.context["request"] = await get_request_context(request)
        if Settings.get().AUTHN_ENGINE == "remote":
            engine: RemoteEngine = AuthorizationEngine.get()  # type: ignore
            assert authorization
            result = engine.is_authorized(
                policy_name=authz_data.policy_name,
                rule=authz_data.rule,
                context=authz_data.context,
                resources=authz_data.resources,
                access_token=authorization.credentials,
                user_email=user_email,
                impersonate_handle=impersonate_entity_handle,
                impersonate_entity_owner=impersonate_entity_owner,
            )
        else:
            entity = EntityDAO.from_handle(
                handle=infostar.user_handle,
                owner_handle=infostar.user_owner_handle,
            )
            if not entity:
                message = (
                    f"Entity not found for handle: {infostar.user_handle}."
                )
                raise HTTPException(
                    status_code=s.HTTP_401_UNAUTHORIZED,
                    detail=dict(msg=message),
                )

            result = await authz_controllers.authorize(
                request,
                entity,
                authz_data,
                allowed_permissions=get_allowed_permissions(request),
            )

        if not result.authorized:
            raise HTTPException(
                status_code=s.HTTP_403_FORBIDDEN, detail=result.details
            )
        request.state.authz_result = result
        return result

    return _authorize
