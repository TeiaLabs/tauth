import contextlib
from datetime import datetime
from hashlib import sha256
from typing import Any, Self

import httpx
import jwt as pyjwt
import pymongo
import pymongo.errors
from fastapi import BackgroundTasks, HTTPException, Request
from fastapi import status as s
from httpx import HTTPError
from jwt import (
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)
from loguru import logger
from pytz import UTC
from redbaby.pyobjectid import PyObjectId

from ...authproviders.models import AuthProviderDAO
from ...schemas import Creator, Infostar
from ...settings import Settings
from ...utils import reading
from ..utils import get_request_ip
from .models import UserInfoDAO
from .schemas import OAuth2Settings
from .utils import (
    get_signing_key,
    get_token_headers,
    get_token_unverified_claims,
    register_user,
)


class UserInfo:
    CACHE_DEFAULT_TIMEOUT = 60 * 60 * 1  # 1h

    @classmethod
    def _cache(
        cls: type[Self],
        access_token: str,
        exp: float | None,
        data: dict[str, Any],
    ):
        """
        Caches the userinfo value.

        :param access_token: Access token.
        :param data: User info data
        :param exp: Cache expiration time. It is based on
            the `exp` claim of the access token.
        """

        coll = UserInfoDAO.collection(alias=Settings.get().REDBABY_ALIAS)

        hashed_token = sha256(access_token.encode()).hexdigest()
        data["hashed_token"] = hashed_token
        if exp is None:
            exp = (
                datetime.now(UTC).timestamp() + UserInfo.CACHE_DEFAULT_TIMEOUT
            )

        # Delete expired caches
        coll.delete_many({"exp": {"$lt": datetime.now(UTC).timestamp()}})

        data["exp"] = exp
        with contextlib.suppress(pymongo.errors.DuplicateKeyError):
            """
            Duplicate key errors will be tolerated given that multiple
            workers are running at the same time and might concurrently
            attempt to create a new record at once.
            """
            coll.insert_one(data)

    @classmethod
    def _try_read(cls: type[Self], access_token: str) -> Any | None:
        """
        Reads a cache from the database if its ttl was not exceeded.

        If the database record has exceeded its ttl, it will return None.

        :param access_token: Access token.
        :return: Cache data found. `None` if not found
        """

        now = datetime.now(UTC).timestamp()
        hashed_token = sha256(access_token.encode()).hexdigest()

        coll = UserInfoDAO.collection(alias=Settings.get().REDBABY_ALIAS)
        value = coll.find_one(
            {
                "hashed_token": hashed_token,
                "exp": {"$gte": now},
            }
        )
        if value:
            value.pop("exp")
            value.pop("hashed_token")

        return value

    @classmethod
    def get_user_info(
        cls: type[Self],
        exp: float | None,
        access_token: str,
        oauth2_settings: OAuth2Settings,
    ):
        user_info = cls._try_read(access_token=access_token)
        if not user_info:
            res = httpx.get(
                oauth2_settings.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            res.raise_for_status()
            user_info = res.json()

            cls._cache(
                access_token=access_token,
                exp=exp,
                data=user_info,
            )

        return user_info


class RequestAuthenticator:
    SUPPORTED_PROVIDERS = ("auth0", "okta")

    @staticmethod
    def get_oauth2_idp(issuer: str | None) -> str:
        logger.debug(f"Inspecting Access token issuer: {issuer!r}.")
        if issuer is None:
            raise HTTPException(
                status_code=s.HTTP_401_UNAUTHORIZED,
                detail={"msg": "Missing 'iss' claim in Access token."},
            )
        for provider in RequestAuthenticator.SUPPORTED_PROVIDERS:
            if provider in issuer:
                logger.debug(f"Authenticating with an {provider!r} provider.")
                return provider

        raise HTTPException(
            status_code=s.HTTP_401_UNAUTHORIZED,
            detail={
                "msg": f"No valid OAuth2 provider found. Got issuer: {issuer!r}."
            },
        )

    @staticmethod
    def get_authprovider(token_value: str, type: str) -> AuthProviderDAO:
        logger.debug(f"Getting {type!r} AuthProvider.")
        filters: dict[str, Any] = {"type": type}

        token_claims = get_token_unverified_claims(token_value)

        matches = []
        if aud := token_claims.get("aud"):
            if isinstance(aud, str):
                aud = [aud]
            # We assume that the actual audience is the first element in the list.
            # Auth0: the second element is the issuer's "userinfo" endpoint.
            matches.append(
                {
                    "$elemMatch": {"name": "audience", "value": aud[0]},
                }
            )

        if org_id := token_claims.get("org_id"):
            matches.append(
                {
                    "$elemMatch": {"name": "org_id", "value": org_id},
                }
            )

        if matches:
            if len(matches) > 1:
                filters["external_ids"] = {"$all": matches}
            else:
                filters["external_ids"] = matches[0]

        provider = reading.read_one_filters(
            infostar={},  # type: ignore
            model=AuthProviderDAO,
            **filters,
        )
        return provider

    @staticmethod
    def validate_access_token(
        token_value: str,
        token_headers: dict[str, Any],
        authprovider: AuthProviderDAO,
        oauth2_settings: OAuth2Settings,
    ) -> dict:
        logger.debug("Validating access token.")
        kid = token_headers.get("kid")
        if kid is None:
            raise InvalidTokenError("Missing 'kid' header.")

        signing_key = get_signing_key(
            kid, oauth2_settings.jwks_url, authprovider.type
        )
        if signing_key is None:
            raise InvalidSignatureError("No signing key found.")

        access_claims = pyjwt.decode(
            token_value,
            signing_key,
            algorithms=[token_headers.get("alg", "RS256")],
            issuer=oauth2_settings.domain,
            audience=oauth2_settings.audience,
            options={"require": ["exp", "iss", "aud"]},
        )
        return access_claims

    @staticmethod
    def assemble_user_data(
        access_claims: dict[str, Any],
        user_info: dict[str, Any],
    ) -> dict:
        logger.debug("Assembling user data.")
        # required_access = ["org_id"]
        required_access = []
        required_id = ["sub", "email"]
        for required_claims, claims in zip(
            [required_access, required_id],
            (access_claims, user_info),
            strict=True,
        ):
            for c in required_claims:
                if c not in claims:
                    raise MissingRequiredClaimError(c)

        user_data = {
            "user_id": user_info.get("sub"),
            "user_email": user_info.get("email"),
        }
        return user_data

    @staticmethod
    def assemble_infostar(
        request: Request, user_data: dict, authprovider: AuthProviderDAO
    ) -> Infostar:
        logger.debug("Assembling Infostar.")
        ip = get_request_ip(request)

        infostar = Infostar(
            request_id=PyObjectId(),
            apikey_name="jwt",
            authprovider_type=authprovider.type,
            authprovider_org=authprovider.organization_ref.handle,
            extra={},
            service_handle=authprovider.service_ref.handle,
            user_handle=user_data["user_email"],
            user_owner_handle=authprovider.organization_ref.handle,
            client_ip=ip,
            original=None,
        )

        return infostar

    @classmethod
    def validate(
        cls,
        request: Request,
        token_value: str,
        background_tasks: BackgroundTasks,
    ):
        try:
            header = get_token_headers(token_value)
            unverified_claims = get_token_unverified_claims(token_value)

            idp_type = cls.get_oauth2_idp(issuer=unverified_claims.get("iss"))
            authprovider = cls.get_authprovider(token_value, idp_type)
            oauth2_settings = OAuth2Settings.from_authprovider(authprovider)

            access_claims = cls.validate_access_token(
                token_value=token_value,
                token_headers=header,
                authprovider=authprovider,
                oauth2_settings=oauth2_settings,
            )
            exp = access_claims.get("exp")
            user_info = UserInfo.get_user_info(
                exp=exp,
                access_token=token_value,
                oauth2_settings=oauth2_settings,
            )
        except (
            MissingRequiredClaimError,
            InvalidTokenError,
            InvalidSignatureError,
            HTTPError,
        ) as e:
            raise HTTPException(
                401,
                detail={
                    "loc": ["headers", "Authorization"],
                    "msg": f"{e.__class__.__name__}: {e}",
                    "type": e.__class__.__name__,
                },
            )
        user_data = cls.assemble_user_data(access_claims, user_info)
        infostar = cls.assemble_infostar(request, user_data, authprovider)
        user_email = user_data["user_email"]
        auth_provider_org_ref = authprovider.organization_ref.model_dump()

        request.state.infostar = infostar
        logger.debug("Assembling Creator based on Infostar.")
        request.state.creator = Creator.from_infostar(infostar)

        background_tasks.add_task(
            register_user,
            user_email,
            auth_provider_org_ref,
            infostar,
        )
