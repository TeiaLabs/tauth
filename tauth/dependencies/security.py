from logging import getLogger
from typing import Iterable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Security
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase
from http_error_schemas.schemas import RequestValidationError

from ..auth import auth0, auth0_dyn, azure_jwt, teia_api_key
from ..settings import Settings

log = getLogger("tauth")


def init_app(app: FastAPI):
    settings = Settings()
    if settings.ENABLE_AUTH0:
        m = f"{auth0.Auth0Settings.__fields__} must be set."
        assert auth0.Auth0Settings().validate(), m
    if settings.ENABLE_AZURE:
        m = f"{azure_jwt.ADAuthSettings.__fields__} must be set."
        assert azure_jwt.ADAuthSettings().validate(), m
    app.router.dependencies.append(Depends(RequestAuthenticator.validate))


class RequestAuthenticator:
    ignore_paths: Iterable[str] = ("/", "/api", "/api/")

    @staticmethod
    def validate(
        request: Request,
        user_email: str | None = Header(
            default=None, alias="X-User-Email", description="Ignore when using OAuth."
        ),
        id_token: str | None = Header(
            default=None, alias="X-ID-Token", description="Auth0 ID token."
        ),
        authorization: HTTPAuthorizationCredentials | None = Security(
            HTTPBase(scheme="bearer", auto_error=False)
        ),
    ):
        # TODO: move empty header check to a subclass of HTTPBase
        req_path: str = request.scope["path"]
        if request.method == "GET" and req_path in RequestAuthenticator.ignore_paths:
            return

        if not authorization:
            d = RequestValidationError(
                loc=["header", "Authorization"],
                msg="Missing Authorization header.",
                type="MissingHeader",
            )
            raise HTTPException(401, detail=d)

        token_type, token_value = authorization.scheme, authorization.credentials
        if token_type.lower() != "bearer":
            raise HTTPException(
                401, detail={"msg": "Invalid authorization scheme; expected 'bearer'."}
            )

        if token_value.startswith("MELT_"):
            log.debug("Authenticating with a TEIA API key.")
            teia_api_key.RequestAuthenticator.validate(request, user_email, token_value)
            return

        if Settings.get().ENABLE_AUTH0 and id_token is not None:
            log.debug("Authenticating with Auth0.")
            auth0.RequestAuthenticator.validate(request, token_value, id_token)
            return

        if Settings.get().ENABLE_AUTH2 and id_token is not None:
            log.debug("Authenticating with Auth2.")
            auth0_dyn.RequestAuthenticator.validate(request, token_value, id_token)
            return

        if Settings.get().ENABLE_AZURE:
            log.debug("Authenticating with an Azure JWT.")
            azure_jwt.RequestAuthenticator.validate(request, token_value)
            return

        raise HTTPException(401, detail={"msg": "No authentication method succeeded."})
