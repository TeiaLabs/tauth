import secrets
from typing import Optional

from fastapi import HTTPException, Request
from fastapi import status as s
from loguru import logger
from pydantic import validate_email
from pymongo.errors import DuplicateKeyError
from redbaby.pyobjectid import PyObjectId

from ...authproviders.models import AuthProviderDAO
from ...controllers import creation, reading
from ...entities.models import EntityDAO, EntityRef
from ...entities.schemas import EntityIntermediate
from ...models.client import UserDAO
from ...schemas import Creator, Infostar
from ...settings import Settings
from .token import parse_token, sanitize_client_name, validate_token_against_db

EmailStr = str


class RequestAuthenticator:
    @staticmethod
    def validate(
        request: Request,
        user_email: str | None,
        api_key_header: str,
    ):
        creator = get_request_creator(token=api_key_header, user_email=user_email)
        infostar = get_request_infostar(creator, request)
        if request.client is not None:
            creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            creator.user_ip = request.headers["x-forwarded-for"]
        request.state.creator = creator
        request.state.infostar = infostar


def get_request_infostar(creator: Creator, request: Request):
    logger.debug("Assembling Infostar based on Creator.")
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


def get_request_creator(token: str, user_email: Optional[str]):
    logger.debug("Parsing token.")
    client_name, token_name, _ = parse_token(token)
    client_name = sanitize_client_name(client_name)
    logger.debug(f"client_name: {client_name!r}, token_name: {token_name!r}")
    token_creator_user_email = None
    if client_name == "/":
        logger.debug("Using root token, checking email.")
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
        logger.debug("Using non-root token, validating token in DB.")
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
    # TODO: create user entity in DB instead
    # create_user_on_db(creator, token_creator_user_email)
    return creator


def create_user_on_db(creator: Creator, token_creator_email: Optional[EmailStr]):
    user_creator_email = (
        creator.user_email if token_creator_email is None else token_creator_email
    )
    try:
        # authprovider_filters = {
        #     "type": "melt-key",
        #     "organization_ref.handle": {"$regex": f"^{creator.client_name}"},
        # }
        # authprovider = reading.read_one_filters(
        #     creator={}, model=AuthProviderDAO, **authprovider_filters
        # )
        organization = f"/{creator.client_name.split("/")[1]}"
        filters_org = {"type": "organization", "handle": organization}
        org_entity = reading.read_one_filters(creator={}, model=EntityDAO, **filters_org)
        org_ref = EntityRef(**org_entity.model_dump())
        user_i = EntityIntermediate(
            handle=creator.user_email,
            # owner_ref=authprovider.organization_ref.model_dump(),  # type: ignore
            owner_ref=org_ref,
            type="user",
        )
        user = creation.create_one(
            user_i,
            EntityDAO,
            creator={
                "client_name": creator.user_email,
                "token_name": creator.client_name,
                "user_email": user_creator_email,
                # "user_ip": "system",
            },  # type: ignore
        )
        logger.debug(f"Registered user {user_creator_email!r} after using authprovider 'melt-key'.")
    except DuplicateKeyError:
        pass
