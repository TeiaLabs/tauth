import secrets
from typing import Optional

from fastapi import HTTPException, Request
from fastapi import status as s
from loguru import logger
from pydantic import validate_email
from redbaby.pyobjectid import PyObjectId

from ...authproviders.models import AuthProviderDAO
from ...authproviders.schemas import AuthProviderMoreIn
from ...entities.models import EntityDAO, EntityRef, OrganizationRef
from ...entities.schemas import EntityIntermediate
from ...schemas import Creator, Infostar
from ...schemas.attribute import Attribute
from ...settings import Settings
from ...utils import creation, reading
from .token import parse_token, sanitize_client_name, validate_token_against_db

EmailStr = str


class RequestAuthenticator:
    @classmethod
    def validate(
        cls,
        request: Request,
        user_email: str | None,
        api_key_header: str,
    ):
        creator, token_creator_user_email = cls.get_request_creator(
            api_key_header, user_email
        )
        infostar = cls.get_request_infostar(creator, request)
        # TODO: create user entity in DB
        cls.create_user_on_db(creator, infostar, token_creator_user_email)

        if request.client is not None:
            creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            creator.user_ip = request.headers["x-forwarded-for"]
        request.state.creator = creator
        request.state.infostar = infostar

    @staticmethod
    def get_token_details(token_value: str) -> tuple[str, str, str]:
        """Returns the client and token name from the token value."""
        logger.debug("Parsing token to extract details.")
        client, name, value = parse_token(token_value)
        client = sanitize_client_name(client)
        logger.debug(f"client_name: {client!r}, token_name: {name!r}")
        return client, name, value

    @staticmethod
    def get_organization_for_client(creator: Creator, infostar: Infostar) -> EntityDAO:
        """Return the organization entity for a given client name."""
        if creator.client_name == "/":
            logger.debug(f"Using root token, org = /.")
            organization = "/"
            org_i = EntityIntermediate(
                handle="/",
                owner_ref=None,
                type="organization",
            )
            try:  # TODO read or create
                org = creation.create_one(org_i, EntityDAO, infostar=infostar)
                logger.debug(f"Created root organization entity.")
            except HTTPException as e:
                if e.status_code != 409:
                    raise e
        logger.debug(f"Getting organization for client {creator.client_name!r}.")
        org_handle = creator.client_name.split("/")[1]
        organization = f"/{org_handle}"
        filters_org = {"type": "organization", "handle": organization}
        org = reading.read_one_filters(
            infostar=infostar, model=EntityDAO, **filters_org
        )
        return org

    @staticmethod
    def get_authprovider(
        organization: EntityDAO, creator: Creator, infostar: Infostar
    ) -> AuthProviderDAO:
        """Return the 'melt-key' AuthProvider for the given client name."""
        logger.debug(f"Getting 'melt-key' provider for org {organization.handle!r}.")
        if organization.handle == "/":
            provider_i = AuthProviderMoreIn(
                organization_ref=OrganizationRef(**organization.model_dump()),
                type="melt-key",
                service_ref=None,
                extra=[Attribute(name="melt_key_client", value="/")],
            )
            try:  # TODO read or create
                provider = creation.create_one(
                    provider_i, AuthProviderDAO, infostar=infostar
                )
                logger.debug(
                    f"Created 'melt-key' provider for org {organization.handle!r}."
                )
            except HTTPException as e:
                if e.status_code != 409:
                    raise e
        filters = {
            "type": "melt-key",
            "organization_ref.handle": organization.handle,
        }
        provider = reading.read_one_filters(infostar, model=AuthProviderDAO, **filters)
        return provider

    @staticmethod
    def get_request_infostar(creator: Creator, request: Request):
        logger.debug("Assembling Infostar based on Creator.")
        breadcrumbs = creator.client_name.split("/")
        owner_handle = f"/{breadcrumbs[1]}"
        service_handle = "--".join(breadcrumbs[2:]) if len(breadcrumbs) > 2 else ""
        infostar = Infostar(
            request_id=PyObjectId(),
            apikey_name=creator.token_name,
            authprovider_type="melt-key",
            authprovider_org=owner_handle,
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

    @classmethod
    def get_request_creator(
        cls, token: str, user_email: Optional[str]
    ) -> tuple[Creator, Optional[EmailStr]]:
        """Returns the Creator and token creator user email for a given request."""
        logger.debug("Getting Creator for request.")
        client_name, token_name, token_value = cls.get_token_details(token)
        token_creator_user_email = None
        if client_name == "/":
            logger.debug("Using root token, checking email.")
            if user_email is None:
                code, m = (
                    s.HTTP_401_UNAUTHORIZED,
                    "User email is required for root client.",
                )
                raise HTTPException(status_code=code, detail=m)
            if not secrets.compare_digest(token, Settings().TAUTH_ROOT_API_KEY):
                print(token_value, Settings().TAUTH_ROOT_API_KEY)
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
                request_creator_user_email = token_obj["created_by"]["user_handle"]
            else:
                token_creator_user_email = token_obj["created_by"]["user_handle"]
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
        return creator, token_creator_user_email

    @classmethod
    def create_user_on_db(
        cls,
        creator: Creator,
        infostar: Infostar,
        token_creator_email: Optional[EmailStr],
    ):
        logger.debug("Registering user.")
        client_org = cls.get_organization_for_client(creator, infostar)
        authprovider = cls.get_authprovider(client_org, creator, infostar)
        org_ref = EntityRef(**client_org.model_dump())
        melt_key_client_extra = Attribute(
            name="melt_key_client", value=creator.client_name
        )
        user_creator_email = (
            creator.user_email if token_creator_email is None else token_creator_email
        )

        user_data = None
        try:
            logger.debug(
                f"Checking if user {user_creator_email!r} exists in org {client_org.handle!r}."
            )
            user_data = reading.read_one_filters(
                infostar,
                model=EntityDAO,
                handle=user_creator_email,
                owner_ref=org_ref.model_dump(),
                type="user",
            )
        except HTTPException as e:
            if e.status_code != 404:
                raise e

        if user_data:
            logger.debug(
                f"User {user_creator_email!r} exists. Adding {creator.client_name!r} client info."
            )
            entity_coll = EntityDAO.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS)
            entity_coll.update_one(
                filter={"_id": user_data.id},
                update={"$addToSet": {"extra": melt_key_client_extra.model_dump()}},
            )
            return

        logger.debug(f"User does not exist. Adding user to DB.")
        user_i = EntityIntermediate(
            handle=creator.user_email,
            owner_ref=org_ref,
            type="user",
            extra=[melt_key_client_extra],
        )
        user = creation.create_one(user_i, EntityDAO, infostar=infostar)
        logger.debug(f"Registered {user_creator_email!r} in org {client_org.handle!r}.")
