import secrets
from typing import Optional

from fastapi import HTTPException, Request
from fastapi import status as s
from multiformats import multibase
from pydantic import EmailStr, validate_email
from redbaby.pyobjectid import PyObjectId

from ..schemas import Creator, Infostar
from ..settings import Settings
from ..utils.access_helper import sanitize_client_name
from ..utils.creator_helper import create_user_on_db, validate_token_against_db
from ..utils.token_helper import parse_token


class RequestAuthenticator:
    @staticmethod
    def validate(
        request: Request,
        user_email: str | None,
        api_key_header: str,
    ):
        creator = get_request_creator(token=api_key_header, user_email=user_email)
        infostar = get_request_infostar(creator, request)
        print(infostar)
        if request.client is not None:
            creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            creator.user_ip = request.headers["x-forwarded-for"]
        request.state.creator = creator
        request.state.infostar = infostar


def get_request_infostar(creator: Creator, request: Request):
    breadcrumbs = creator.client_name.split("/")
    owner_handle = f"/{breadcrumbs[1]}"
    service_handle = "--".join(breadcrumbs[2:]) if len(breadcrumbs) > 2 else ""
    infostar = Infostar(
        request_id=PyObjectId(),
        apikey_name=creator.token_name,
        authprovider_type="melt-api-key",
        authprovider_org="/teialabs",
        # extra=InfostarExtra(
        #     geolocation=request.headers.get("x-geo-location"),
        #     jwt_sub=request.headers.get("x-jwt-sub"),
        #     os=request.headers.get("x-os"),
        #     url=request.headers.get("x-url"),
        #     user_agent=request.headers.get("user-agent"),
        # ),
        extra={},
        original=None,
        service_handle=service_handle,
        user_handle=creator.user_email,
        user_owner_handle=owner_handle,
        client_ip=creator.user_ip,
    )
    return infostar


def parse_token(token_value: str) -> tuple[str, str, str]:
    """
    Parse token string into client name, token name, and token value.

    Raise an error if token is incorrectly formatted.
    >>> parse_token("MELT_/client-name--token-name--abcdef123456789")
    ('client-name', 'token-name', 'abcdef123456789')
    """
    stripped = token_value.lstrip("MELT_")
    pieces = stripped.split("--")
    if len(pieces) != 3:
        code, m = 401, "Token is not in the correct format."
        raise HTTPException(status_code=code, detail=m)
    return tuple(pieces)  # type: ignore


def create_token(client_name: str, token_name: str):
    token_value = multibase.encode(secrets.token_bytes(24), "base58btc")
    fmt_token_value = f"MELT_{client_name}--{token_name}--{token_value}"
    return fmt_token_value


def get_request_creator(token: str, user_email: Optional[str]):
    client_name, token_name, _ = parse_token(token)
    client_name = sanitize_client_name(client_name)
    token_creator_user_email = None
    if client_name == "/":
        if user_email is None:
            code, m = s.HTTP_401_UNAUTHORIZED, "User email is required for root client."
            raise HTTPException(status_code=code, detail=m)
        if not secrets.compare_digest(token, Settings().TAUTH_ROOT_API_KEY):
            code, m = s.HTTP_401_UNAUTHORIZED, "Root token does not match env var."
            raise HTTPException(status_code=code, detail=m)
        try:
            validate_email(user_email)
        except:
            code, m = s.HTTP_401_UNAUTHORIZED, "User email is not valid."
            raise HTTPException(status_code=code, detail=m)
        request_creator_user_email = user_email
    else:
        token_obj = validate_token_against_db(token, client_name, token_name)
        if user_email is None:
            request_creator_user_email = token_obj["created_by"]["user_email"]
        else:
            token_creator_user_email = token_obj["created_by"]["user_email"]
            try:
                validate_email(user_email)
            except:
                code, m = s.HTTP_401_UNAUTHORIZED, "User email is not valid."
                raise HTTPException(status_code=code, detail=m)
            request_creator_user_email = user_email
    creator = Creator(
        client_name=client_name,
        token_name=token_name,
        user_email=request_creator_user_email,
    )
    create_user_on_db(creator, token_creator_user_email)
    return creator
