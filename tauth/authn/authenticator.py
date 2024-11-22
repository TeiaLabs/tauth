from collections.abc import Iterable

from fastapi import BackgroundTasks, HTTPException, Request
from fastapi import status as s
from fastapi.security.http import HTTPAuthorizationCredentials
from http_error_schemas.schemas import RequestValidationError
from loguru import logger

from tauth.settings import Settings
from tauth.utils.headers import auth_headers_injector

from ..authn.melt_key import authentication as melt_key
from ..authn.oauth2 import authentication as oauth2
from ..authn.remote import engine as remote


def authn(ignore_paths: Iterable[str] = ("/", "/api", "/api/")):
    @auth_headers_injector
    def _authenticate(
        request: Request,
        background_tasks: BackgroundTasks,
        user_email: str | None = None,
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
            raise HTTPException(s.HTTP_401_UNAUTHORIZED, detail=d)

        token_type, token_value = (
            authorization.scheme,
            authorization.credentials,
        )
        if token_type.lower() != "bearer":
            raise HTTPException(
                s.HTTP_401_UNAUTHORIZED,
                detail={"msg": "Invalid authorization scheme; expected 'bearer'."},
            )

        if Settings.get().AUTHN_ENGINE == "remote":
            logger.debug("Authenticating with a Remote Auth (new ⚡).")
            remote.RequestAuthenticator.validate(
                request=request,
                access_token=token_value,
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

        oauth2.RequestAuthenticator.validate(
            request=request,
            token_value=token_value,
            background_tasks=background_tasks,
        )

    return _authenticate
