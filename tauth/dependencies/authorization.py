import asyncio
from collections.abc import Callable

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

from tauth.authn.routes import authenticate
from tauth.authz import controllers as authz_controllers
from tauth.authz.policies.schemas import AuthorizationDataIn
from tauth.schemas.infostar import Infostar
from tauth.utils.headers import auth_headers_injector

from ..authz.engines.factory import AuthorizationEngine
from ..authz.engines.interface import AuthorizationResponse


def setup_engine():
    AuthorizationEngine.setup()


def init_app(app: FastAPI):
    app.router.dependencies.append(
        Depends(_authorize_no_return, use_cache=True)
    )


def init_router(router: APIRouter):
    router.dependencies.append(Depends(_authorize_no_return, use_cache=True))


def authorize(
    authz_data: AuthorizationDataIn,
    infostar: Infostar = Depends(authenticate),
) -> Callable[[], AuthorizationResponse]:
    print("Aqui")

    def wrapper(authz_response=Depends(_authorize)):
        return authz_response

    return wrapper


@auth_headers_injector
def _authorize(
    request: Request,
    background_tasks: BackgroundTasks,
    user_email: str | None = None,
    id_token: str | None = None,
    authorization: HTTPAuthorizationCredentials | None = None,
    authz_data: AuthorizationDataIn | None = None,
) -> AuthorizationResponse:
    print("Ali")
    if not authz_data:
        raise HTTPException(
            status_code=s.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid or missing authorization data.",
        )
    result = asyncio.run(authz_controllers.authorize(request, authz_data))
    if not result.authorized:
        raise HTTPException(
            status_code=s.HTTP_403_FORBIDDEN, detail=result.details
        )
    return result


def _authorize_no_return(_=Depends(_authorize)) -> None:
    pass
