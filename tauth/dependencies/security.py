from logging import getLogger
from typing import Iterable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Security
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase
from http_error_schemas.schemas import RequestValidationError

from ..auth import auth0, auth0_dyn, azure_jwt, melt_api_key
from ..settings import Settings

log = getLogger("tauth")


def init_app(app: FastAPI):
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
            melt_api_key.RequestAuthenticator.validate(request, user_email, token_value)
            return
        # TODO: check if it starts with TAUTH_
        # TODO: check if it's a JWT
        # figure out which provider/iss it's from
        # audience too

        raise HTTPException(401, detail={"msg": "No authentication method succeeded."})
