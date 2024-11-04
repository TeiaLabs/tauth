from collections.abc import Callable

from fastapi import Header, HTTPException, Security
from fastapi import status as s
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase

from ..authz.engines.factory import AuthorizationEngine
from ..authz.engines.interface import AuthorizationResponse


def init_app():
    AuthorizationEngine.setup()


def authorize(
    policy_name: str,
    resource: str,
) -> Callable[..., AuthorizationResponse]:
    AuthorizationEngine.setup()
    engine = AuthorizationEngine.get()

    def wrap(
        user_email: str | None = Header(
            default=None,
            alias="X-User-Email",
            description="Ignore when using OAuth.",
        ),
        id_token: str | None = Header(
            default=None, alias="X-ID-Token", description="Auth0 ID token."
        ),
        authorization: HTTPAuthorizationCredentials | None = Security(
            HTTPBase(scheme="bearer", auto_error=False)
        ),
    ):
        response = engine.is_authorized(
            policy_name=policy_name,
            rule=resource,
            access_token=f"{authorization.scheme} {authorization.credentials}",
            id_token=id_token,
            user_email=user_email,
        )
        if not response.authorized:
            raise HTTPException(
                status_code=s.HTTP_403_FORBIDDEN, detail=response.details
            )
        return response

    return wrap
