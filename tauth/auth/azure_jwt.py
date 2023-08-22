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
from httpx import Client
from pydantic import BaseSettings, root_validator

from ..schemas import Creator

log = getLogger("tauth")


class ADAuthSettings(BaseSettings):
    AZURE_AD_AUDIENCE: str = ""
    AZURE_AD_TENANT: str = ""

    def validate(self):
        for k, v in self.__fields__.items():
            if k.startswith("AZURE") and not getattr(self, k):
                raise ValueError(f"Variable {k} cannot be empty.")
        return True

    class Config:
        env_file = ".env"


class TenantKeyStore:
    tenant_id: str = ADAuthSettings().AZURE_AD_TENANT

    @classmethod
    @ttl_cache(maxsize=1, ttl=60 * 60 * 24)
    def get_jwk(cls) -> KeySet:
        log.debug("Fetching JWK.")
        with Client() as client:
            res = client.get(
                f"https://login.microsoftonline.com/{cls.tenant_id}/discovery/v2.0/keys"
            )
            res.raise_for_status()
            log.info("JWK fetched from Azure AD.")
            return JsonWebKey.import_key_set(res.json())


def init_app(app: FastAPI):
    app.router.dependencies.append(Depends(RequestAuthenticator.validate))


class RequestAuthenticator:
    settings = ADAuthSettings()
    claims_options = {
        "aud": {"essential": True, "value": settings.AZURE_AD_AUDIENCE},
        "iss": {
            "essential": True,
            "value": f"https://sts.windows.net/{settings.AZURE_AD_TENANT}/",
        },
        "exp": {"essential": True},
    }

    @staticmethod
    def validate(request: Request, token_value: str):
        json_web_key = TenantKeyStore.get_jwk()
        try:
            claims = jwt.decode(
                token_value,
                json_web_key,
                claims_options=RequestAuthenticator.claims_options,
            )
            claims.validate()
        except (
            ExpiredTokenError,
            InvalidClaimError,
            InvalidTokenError,
            MissingClaimError,
        ) as e:
            raise HTTPException(401, detail={"msg": e.description, "type": e.error})
        except Exception as e:
            raise HTTPException(401, detail={"msg": str(e), "type": type(e).__name__})

        oid: str | None = claims.get("oid")
        if not oid:
            d = {"msg": "Missing 'oid' claim.", "type": "MissingRequiredClaim"}
            raise HTTPException(401, detail=d)

        user_email = claims.get("email")
        if not user_email:
            d = {"msg": "Missing 'email' claim.", "type": "MissingRequiredClaim"}
            raise HTTPException(401, detail=d)
        request.state.creator = Creator(
            client_name="/osf/wingman",
            token_name="azure-jwt",
            user_email=user_email,
        )
        # TODO: forward user IP using a header
        if request.client is not None:
            request.state.creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            request.state.creator.user_ip = request.headers["x-forwarded-for"]
