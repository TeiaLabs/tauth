from logging import getLogger
from typing import Optional, Self

from authlib.jose import jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    InvalidTokenError,
    JoseError,
    MissingClaimError,
)
from authlib.jose.rfc7517.jwk import JsonWebKey, KeySet
from cachetools.func import ttl_cache
from fastapi import HTTPException, Request
from httpx import Client, HTTPError
from pydantic import BaseModel

from ..authproviders.models import AuthProviderDAO
from ..controllers import reading
from ..organizations import controllers as org_controllers
from ..schemas import Creator

log = getLogger(__name__)


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


class ManyJSONKeyStore:

    @classmethod
    @ttl_cache(maxsize=16, ttl=60 * 60 * 6)
    def get_jwk(cls, domain: str) -> KeySet:
        log.debug("Fetching JWK.")
        with Client() as client:
            res = client.get(f"https://{domain}/.well-known/jwks.json")
        try:
            res.raise_for_status()
        except HTTPError as e:
            log.error(f"Failed to fetch JWK from {domain}.")
            raise e
        log.info(f"JWK fetched from {domain}.")
        return JsonWebKey.import_key_set(res.json())


class RequestAuthenticator:

    @staticmethod
    def get_id_claims(domain: str) -> dict:
        id_claims_options = {
            "iss": {"essential": True, "value": f"https://{domain}/"},
            "exp": {"essential": True},
        }
        return id_claims_options

    @staticmethod
    def get_access_claims(domain: str, audience: str) -> dict:
        access_claims_options = {
            "aud": {"essential": True, "value": audience},
            "exp": {"essential": True},
            "iss": {"essential": True, "value": f"https://{domain}/"},
        }
        return access_claims_options

    @staticmethod
    def get_authprovider(token_value: str) -> list[AuthProviderDAO]:
        jwt_header = get_unverified_claims(token_value)  # TODO
        filters = {"type": "auth0"}
        if aud := jwt_header.get("aud"):
            filters["external_ids.name"] = "audience"
            filters["external_ids.value"] = aud
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
        return providers

    @staticmethod
    def validate_access_token(
        token_value: str, authprovider: AuthProviderDAO
    ) -> dict | JoseError:
        sets = Auth0Settings.from_authprovider(authprovider)
        j_w_k = ManyJSONKeyStore.get_jwk(sets.domain)
        try:
            access_claims = jwt.decode(
                token_value,
                j_w_k,
                claims_options=RequestAuthenticator.get_access_claims(
                    sets.domain, sets.audience
                ),
            )
            access_claims.validate()
        except (
            ExpiredTokenError,
            InvalidClaimError,
            InvalidTokenError,
            MissingClaimError,
        ) as e:
            # TODO log e.error, e.description, e.uri
            # short-string error code
            # long-string to describe this error
            # web page that describes this error
            return e
        return access_claims

    @staticmethod
    def validate_id_token(token_value: str, authprovider: AuthProviderDAO) -> dict:
        sets = Auth0Settings.from_authprovider(authprovider)
        j_w_k = ManyJSONKeyStore.get_jwk(sets.domain)
        id_claims = jwt.decode(
            token_value,
            j_w_k,
            claims_options=RequestAuthenticator.get_id_claims(sets.domain),
        )
        id_claims.validate()
        return id_claims

    @staticmethod
    def assemble_user_data(access_claims, id_claims) -> dict:
        required_access = ["org_id"]
        required_id = ["sub", "email"]
        for required_claims, claims in zip([required_access, required_id], (access_claims, id_claims)):
            for c in required_claims:
                if c not in claims:
                    raise HTTPException(
                        401,
                        detail={
                            "loc": ["headers", "X-ID-Token" if claims == id_claims else "Authorization"],
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
        if authprovider.service_ref is None:
            raise HTTPException(
                401,
                detail={"msg": "Authprovider has no service reference.", "details": authprovider.model_dump()},
            )
        org = org_controllers.read_one({"$regex": r"/.*--auth0-org-id"}, user_data["org_id"])
        if not org:
            raise HTTPException(
                401, detail=f"Organization with id '{user_data['org_id']}' not found."
            )
        c = Creator(
            client_name=org["name"]
            + authprovider.service_ref.handle,
            token_name="auth0-jwt",
            user_email=user_data["user_email"],
        )
        return c

    @classmethod
    def validate(cls, request: Request, token_value: str, id_token: str):
        auth0_providers = cls.get_authprovider(token_value)
        if len(auth0_providers) >= 1:
            print("Bad. Don't.")
            return
        else:
            authprovider = auth0_providers[0]
        result = cls.validate_access_token(token_value, authprovider)
        if isinstance(result, JoseError):
            raise HTTPException(
                401,
                detail={
                    "loc": ["headers", "Authorization"],
                    "msg": result.description,
                    "type": result.error,
                },
            )
        else:
            access_claims = result
        result = cls.validate_id_token(id_token, authprovider)
        if isinstance(result, JoseError):
            raise HTTPException(
                401,
                detail={
                    "loc": ["headers", "X-ID-Token"],
                    "msg": result.description,
                    "type": result.error,
                },
            )
        else:
            id_claims = result
        user_data = cls.assemble_user_data(access_claims, id_claims)
        request.state.creator = cls.assemble_creator(user_data, authprovider)
        # TODO: forward user IP using a header?
        if request.client is not None:
            request.state.creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            request.state.creator.user_ip = request.headers["x-forwarded-for"]
        return
