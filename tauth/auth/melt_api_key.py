import secrets
from typing import Optional

from pydantic import EmailStr
from fastapi import HTTPException, Request
from fastapi import status as s
from multiformats import multibase
from pydantic import validate_email

from ..schemas import Creator
from ..schemas import Infostar
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
        creator, token_creator_email = get_request_creator(token=api_key_header, user_email=user_email)
        # infostar = get_request_infostar(creator, token_creator_email, request)
        if request.client is not None:
            creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            creator.user_ip = request.headers["x-forwarded-for"]
        request.state.creator = creator


# def get_request_infostar(creator: Creator, token_creator_email: str, request: Request):
#     infostar = Infostar(
#     )
#     return infostar


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
            request_creator_user_email = token_obj.created_by.user_email
        else:
            token_creator_user_email = token_obj.created_by.user_email
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
    return creator, token_obj.created_by.user_email
