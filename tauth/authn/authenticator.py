from collections.abc import Iterable

from fastapi import BackgroundTasks, HTTPException, Request
from fastapi.security.http import HTTPAuthorizationCredentials
from http_error_schemas.schemas import RequestValidationError
from loguru import logger

from tauth.settings import Settings
from tauth.utils.headers import auth_headers_injector

from ..authn import auth0_dyn
from ..authn.melt_key import authentication as melt_key
from ..authn.remote import engine as remote


def authn(ignore_paths: Iterable[str] = ("/", "/api", "/api/")):

    @auth_headers_injector
    def _authenticate(
        request: Request,
        background_tasks: BackgroundTasks,
        user_email: str | None = None,
        id_token: str | None = None,
        authorization: HTTPAuthorizationCredentials | None = None,
    ) -> None:

        req_path: str = request.scope["path"]
        if request.method == "GET" and req_path in ignore_paths:
            return

        if not authorization:
            d = RequestValidationError(
                loc=["header", "Authorization"],
                msg="Missing Authorization header.",
                type="MissingHeader",
            )
            raise HTTPException(401, detail=d)

        token_type, token_value = (
            authorization.scheme,
            authorization.credentials,
        )
        if token_type.lower() != "bearer":
            raise HTTPException(
                401,
                detail={
                    "msg": "Invalid authorization scheme; expected 'bearer'."
                },
            )

        if Settings.get().AUTHN_ENGINE == "remote":
            logger.debug("Authenticating with a Remote Auth (new ⚡).")
            remote.RequestAuthenticator.validate(
                request=request,
                access_token=token_value,
                id_token=id_token,
                user_email=user_email,
            )
            return

        if token_value.startswith("MELT_"):
            logger.debug("Authenticating with a MELT API key (legacy).")
            melt_key.RequestAuthenticator.validate(
                request=request,
                user_email=user_email,
                api_key_header=token_value,
                background_tasks=background_tasks,
            )
            return

        if id_token is None:
            raise HTTPException(401, detail={"msg": "Missing ID token."})
        else:
            logger.debug("Authenticating with an Auth0 provider.")
            # figure out which provider/iss it's from
            auth0_dyn.RequestAuthenticator.validate(
                request=request,
                token_value=token_value,
                id_token=id_token,
                background_tasks=background_tasks,
            )
            return

    return _authenticate
