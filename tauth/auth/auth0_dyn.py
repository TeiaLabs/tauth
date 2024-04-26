from typing import Any, Optional, Self

import jwt as pyjwt
from cachetools.func import ttl_cache
from fastapi import HTTPException, Request
from httpx import Client, HTTPError
from jwt import (
    InvalidSignatureError,
    InvalidTokenError,
    PyJWKClient,
    PyJWKSet,
    PyJWTError,
)
from loguru import logger
from pydantic import BaseModel

from ..authproviders.models import AuthProviderDAO
from ..controllers import reading
from ..organizations import controllers as org_controllers
from ..schemas import Creator


def get_token_headers(token: str) -> dict[str, Any]:
    header = pyjwt.get_unverified_header(token)
    return header


def get_token_unverified_claims(token: str) -> dict[str, Any]:
    claims = pyjwt.decode(token, options={"verify_signature": False})
    return claims


def get_signing_key(kid: str, domain: str) -> Optional[str]:
    jwk_set = ManyJSONKeySetStore.get_jwks(domain)
    signing_key = PyJWKClient.match_kid(jwk_set.keys, kid)
    return signing_key.key.public_key() if signing_key else None


class Auth0Settings(BaseModel):
    domain: str
    audience: str

    @classmethod
    def from_authprovider(cls, authprovider: AuthProviderDAO) -> Self:
        iss = authprovider.get_external_id("issuer")
        if not iss:
            raise ValueError("Missing 'issuer' attribute.")
        aud = authprovider.get_external_id("audience")
        if not aud:
            raise ValueError("Missing 'audience' attribute.")
        return cls(domain=iss, audience=aud)


class ManyJSONKeySetStore:
    @classmethod
    @ttl_cache(maxsize=16, ttl=60 * 60 * 6)
    def get_jwks(cls, domain: str) -> PyJWKSet:
        logger.debug(f"Fetching JWKS from {domain}.")
        with Client() as client:
            res = client.get(f"{domain}.well-known/jwks.json")
        try:
            res.raise_for_status()
        except HTTPError as e:
            logger.error(f"Failed to fetch JWKS from {domain}.")
            raise e
        logger.debug(f"JWK fetched from {domain}.")

        return PyJWKSet.from_dict(res.json())


class RequestAuthenticator:
    @staticmethod
    def get_authprovider(token_value: str) -> AuthProviderDAO:
        token_claims = get_token_unverified_claims(token_value)
        filters: dict[str, Any] = {"type": "auth0"}
        if aud := token_claims.get("aud"):
            # We assume that the actual audience is the first element in the list.
            # The second element is the issuer's "userinfo" endpoint.
            filters["external_ids"] = {
                "$elemMatch": {"name": "audience", "value": aud[0]}
            }

        providers = reading.read_many(creator={}, model=AuthProviderDAO, **filters)
        if not providers:
            raise HTTPException(
                401,
                detail={
                    "loc": ["headers", "Authorization"],
                    "msg": f"No Auth0 provider found .",
                    "type": "NoAuthProviderFound",
                    "filters": filters,
                },
            )
        return providers[0]

    @staticmethod
    def validate_access_token(
        token_value: str,
        token_headers: dict[str, Any],
        authprovider: AuthProviderDAO,
    ) -> dict | PyJWTError:
        sets = Auth0Settings.from_authprovider(authprovider)
        kid = token_headers.get("kid")
        if kid is None:
            raise InvalidTokenError("Missing 'kid' header.")

        signing_key = get_signing_key(kid, sets.domain)
        if signing_key is None:
            raise InvalidSignatureError("No signing key found.")

        try:
            access_claims = pyjwt.decode(
                token_value,
                signing_key,
                algorithms=[token_headers.get("alg", "RS256")],
                issuer=sets.domain,
                audience=sets.audience,
                options={"require": ["exp", "iss", "aud"]},
            )
        except PyJWTError as e:
            # TODO log e.error, e.description, e.uri
            # short-string error code
            # long-string to describe this error
            # web page that describes this error
            logger.error(f"Failed to validate access token:\n{e}")
            return e
        return access_claims

    @staticmethod
    def validate_id_token(
        token_value: str,
        token_headers: dict[str, Any],
        authprovider: AuthProviderDAO,
    ) -> dict:
        sets = Auth0Settings.from_authprovider(authprovider)
        kid = token_headers.get("kid")
        if kid is None:
            raise InvalidTokenError("Missing 'kid' header.")

        signing_key = get_signing_key(kid, sets.domain)
        if signing_key is None:
            raise InvalidSignatureError("No signing key found.")

        id_claims = pyjwt.decode(
            token_value,
            signing_key,
            algorithms=[token_headers.get("alg", "RS256")],
            issuer=sets.domain,
            audience=sets.audience,
            options={"require": ["iss", "exp"]},
        )
        return id_claims

    @staticmethod
    def assemble_user_data(access_claims, id_claims) -> dict:
        required_access = ["org_id"]
        required_id = ["sub", "email"]
        for required_claims, claims in zip(
            [required_access, required_id], (access_claims, id_claims)
        ):
            for c in required_claims:
                if c not in claims:
                    raise HTTPException(
                        401,
                        detail={
                            "loc": [
                                "headers",
                                (
                                    "X-ID-Token"
                                    if claims == id_claims
                                    else "Authorization"
                                ),
                            ],
                            "msg": f"Missing '{c}' claim.",
                            "type": "MissingRequiredClaim",
                        },
                    )

        user_data = {
            "user_id": id_claims.get("sub"),
            "user_email": id_claims.get("email"),
            "org_id": access_claims.get("org_id"),
        }
        return user_data

    @staticmethod
    def assemble_creator(user_data: dict, authprovider: AuthProviderDAO) -> Creator:
        # if authprovider.service_ref is None:
        #     raise HTTPException(
        #         401,
        #         detail={
        #             "msg": "Authprovider has no service reference.",
        #             "details": authprovider.model_dump(),
        #         },
        #     )
        # TODO: use iss to map to org-name
        org = org_controllers.read_one(
            {"$regex": r"/.*--auth0-org-id"}, user_data["org_id"]
        )
        if not org:
            raise HTTPException(
                401, detail=f"Organization with id '{user_data['org_id']}' not found."
            )

        c = Creator(
            client_name=org["name"]
            + "/happyservice",  # authprovider.service_ref.handle,
            token_name="auth0-jwt",
            user_email=user_data["user_email"],
        )
        return c

    @classmethod
    def validate(cls, request: Request, token_value: str, id_token: str):
        header = get_token_headers(token_value)

        authprovider = cls.get_authprovider(token_value)
        result = cls.validate_access_token(token_value, header, authprovider)
        if isinstance(result, PyJWTError):
            raise HTTPException(
                401,
                detail={
                    "loc": ["headers", "Authorization"],
                    "msg": str(result),
                    "type": str(type(result)),
                },
            )
        else:
            access_claims = result

        result = cls.validate_id_token(id_token, header, authprovider)
        if isinstance(result, PyJWTError):
            raise HTTPException(
                401,
                detail={
                    "loc": ["headers", "X-ID-Token"],
                    "msg": str(result),
                    "type": str(type(result)),
                },
            )
        else:
            id_claims = result

        user_data = cls.assemble_user_data(access_claims, id_claims)
        request.state.creator = cls.assemble_creator(user_data, authprovider)
        request.state.infostar = ""  # TODO
        # TODO: forward user IP using a header?
        if request.client is not None:
            request.state.creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            request.state.creator.user_ip = request.headers["x-forwarded-for"]
