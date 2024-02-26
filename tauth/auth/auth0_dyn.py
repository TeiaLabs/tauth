from logging import getLogger

from authlib.jose import jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    InvalidTokenError,
    MissingClaimError,
)
from authlib.jose.rfc7517.jwk import JsonWebKey, KeySet
from cachetools.func import ttl_cache
from fastapi import HTTPException, Request
from httpx import Client, HTTPError
from pydantic import BaseSettings

from ..schemas import Creator

log = getLogger(__name__)


class Auth0Settings(BaseSettings):
    AUTH2_DOMAIN: str = ""
    AUTH2_AUDIENCE: str = ""

    def validate(self):
        return True

    class Config:
        env_file = ".env"


class ManyJSONKeyStore:
    domains: dict[str, str] = {"/osf/allai/chat/webui": Auth0Settings().AUTH2_DOMAIN}

    @classmethod
    @ttl_cache(maxsize=1, ttl=60 * 60 * 6)
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

    @classmethod
    def get_jwks(cls) -> dict[str, KeySet]:
        return {k: cls.get_jwk(v) for k, v in cls.domains.items()}


class RequestAuthenticator:
    settings = Auth0Settings()
    access_claims_options = {
        "aud": {"essential": True, "value": settings.AUTH2_AUDIENCE},
        "exp": {"essential": True},
        "iss": {"essential": True, "value": f"https://{settings.AUTH2_DOMAIN}/"},
    }
    id_claims_options = {
        "iss": {"essential": True, "value": f"https://{settings.AUTH2_DOMAIN}/"},
        "exp": {"essential": True},
    }

    @staticmethod
    def validate(request: Request, token_value: str, id_token: str):
        for client_name, j_w_k in ManyJSONKeyStore.get_jwks().items():
            try:
                access_claims = jwt.decode(
                    token_value,
                    j_w_k,
                    claims_options=RequestAuthenticator.access_claims_options,
                )
                access_claims.validate()
            except (
                ExpiredTokenError,
                InvalidClaimError,
                InvalidTokenError,
                MissingClaimError,
            ) as e:
                raise HTTPException(
                    401,
                    detail={
                        "loc": ["headers", "Authorization"],
                        "msg": e.description,
                        "type": e.error,
                    },
                )
            except Exception as e:
                raise HTTPException(
                    401,
                    detail={
                        "loc": ["headers", "Authorization"],
                        "msg": str(e),
                        "type": type(e).__name__,
                    },
                )
            try:
                id_claims = jwt.decode(
                    id_token,
                    j_w_k,
                    claims_options=RequestAuthenticator.id_claims_options,
                )
                id_claims.validate()
            except (
                MissingClaimError,
                InvalidClaimError,
                InvalidTokenError,
                ExpiredTokenError,
            ) as e:
                raise HTTPException(
                    401,
                    detail={
                        "loc": ["headers", "X-ID-Token"],
                        "msg": e.description,
                        "type": e.error,
                    },
                )
            except Exception as e:
                raise HTTPException(
                    401,
                    detail={
                        "loc": ["headers", "X-ID-Token"],
                        "msg": str(e),
                        "type": type(e).__name__,
                    },
                )
            user_id = id_claims.get("sub")
            if not user_id:
                raise HTTPException(
                    401,
                    detail={
                        "loc": ["headers", "X-ID-Token"],
                        "msg": "Missing 'sub' claim.",
                        "type": "MissingRequiredClaim",
                    },
                )
            user_email = id_claims.get("email")
            if not user_email:
                d = {
                    "loc": ["headers", "X-ID-Token"],
                    "msg": "Missing 'email' claim.",
                    "type": "MissingRequiredClaim",
                }
                raise HTTPException(401, detail=d)
            request.state.creator = Creator(
                client_name=client_name,
                token_name="auth0-jwt",
                user_email=user_email,
            )
            # TODO: forward user IP using a header?
            if request.client is not None:
                request.state.creator.user_ip = request.client.host
            if request.headers.get("x-forwarded-for"):
                request.state.creator.user_ip = request.headers["x-forwarded-for"]
            return
