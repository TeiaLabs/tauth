from logging import getLogger
from typing import Iterable

from authlib.jose import jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    InvalidTokenError,
    MissingClaimError,
)
from authlib.jose.rfc7517.jwk import JsonWebKey, KeySet
from cachetools.func import ttl_cache
from fastapi.security.http import HTTPBase, HTTPAuthorizationCredentials
from fastapi import Depends, FastAPI, Request, Security, HTTPException
from httpx import Client, HTTPError
from pydantic import BaseSettings, root_validator

from ..schemas import Creator

log = getLogger(__name__)


class Auth0Settings(BaseSettings):
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""

    def validate(self):
        for k, v in self.__fields__.items():
            if k.startswith("AUTH0") and not getattr(self, k):
                raise ValueError(f"Variable {k} cannot be empty.")
        return True

    class Config:
        env_file = ".env"


class JSONKeyStore:
    domain: str = Auth0Settings().AUTH0_DOMAIN

    @classmethod
    @ttl_cache(maxsize=1, ttl=60 * 60 * 6)
    def get_jwk(cls) -> KeySet:
        log.debug("Fetching JWK.")
        with Client() as client:
            res = client.get(f"https://{cls.domain}/.well-known/jwks.json")
        try:
            res.raise_for_status()
        except HTTPError as e:
            log.error(f"Failed to fetch JWK from {cls.domain}.")
            raise e
        log.info(f"JWK fetched from {cls.domain}.")
        return JsonWebKey.import_key_set(res.json())


class RequestAuthenticator:
    settings = Auth0Settings()
    access_claims_options = {
        "aud": {"essential": True, "value": settings.AUTH0_AUDIENCE},
        "exp": {"essential": True},
        "iss": {"essential": True, "value": f"https://{settings.AUTH0_DOMAIN}/"},
    }
    id_claims_options = {
        "iss": {"essential": True, "value": f"https://{settings.AUTH0_DOMAIN}/"},
        "exp": {"essential": True},
    }

    @staticmethod
    def validate(request: Request, token_value: str, id_token: str):
        json_web_key = JSONKeyStore.get_jwk()
        try:
            access_claims = jwt.decode(
                token_value,
                json_web_key,
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
                json_web_key,
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
            d = {"loc": ["headers", "X-ID-Token"], "msg": "Missing 'email' claim.", "type": "MissingRequiredClaim"}
            raise HTTPException(401, detail=d)
        request.state.creator = Creator(
            client_name="/osf/wingman",
            token_name="auth0-jwt",
            user_email=user_email,
        )
        # TODO: forward user IP using a header?
        if request.client is not None:
            request.state.creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            request.state.creator.user_ip = request.headers["x-forwarded-for"]
