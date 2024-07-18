from typing import Iterable

from fastapi import FastAPI, Header, HTTPException, Request, Security
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase
from http_error_schemas.schemas import RequestValidationError
from loguru import logger

from ..authn import auth0_dyn
from ..authn.melt_key import authentication as melt_key


def init_app(app: FastAPI):
    from tauth.utils.fastapi_extension import get_depends

    app.router.dependencies.append(get_depends())


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
            logger.debug("Authenticating with a MELT API key (legacy).")
            melt_key.RequestAuthenticator.validate(request, user_email, token_value)
            return
        if id_token is None:
            raise HTTPException(401, detail={"msg": "Missing ID token."})
        else:
            logger.debug("Authenticating with an Auth0 provider.")
            # figure out which provider/iss it's from
            auth0_dyn.RequestAuthenticator.validate(request, token_value, id_token)
            return
        # TODO: check if it starts with TAUTH_
        # TODO: check if it's a JWT

        raise HTTPException(401, detail={"msg": "No authentication method succeeded."})
