from authlib.jose import jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    InvalidTokenError,
    MissingClaimError,
)
from authlib.jose.rfc7517.jwk import JsonWebKey, KeySet
from httpx import Client
from pydantic import BaseSettings, root_validator
from starlite import (
    AbstractAuthenticationMiddleware,
    ASGIConnection,
    AuthenticationResult,
    NotAuthorizedException,
)


class ADAuthSettings(BaseSettings):
    AZURE_AD_TENANT: str = ""
    AZURE_AD_AUDIENCE: str = ""

    @root_validator()
    def check_non_empty(cls, values):
        for k, v in values.items():
            if not v:
                raise ValueError(f"Variable {k} cannot be empty.")
        return values


settings = ADAuthSettings()


def get_keys(tenant: str) -> KeySet:
    with Client() as client:
        res = client.get(
            f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
        )
        res.raise_for_status()
        return JsonWebKey.import_key_set(res.json())


jwk = get_keys(settings.AZURE_AD_TENANT)
claims_options = {
    "aud": {"essential": True, "value": settings.AZURE_AD_AUDIENCE},
    "iss": {
        "essential": True,
        "value": f"https://sts.windows.net/{settings.AZURE_AD_TENANT}/",
    },
    "exp": {"essential": True},
}


class AuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(
        self, connection: ASGIConnection
    ) -> AuthenticationResult:
        authorization_header = connection.headers.get("Authorization")
        if not authorization_header:
            raise NotAuthorizedException()

        token_parts = authorization_header.split(None, 1)
        if len(token_parts) != 2:
            raise NotAuthorizedException()

        token_type, token_string = token_parts

        if token_type.lower() != "bearer":
            raise NotAuthorizedException()

        try:
            claims = jwt.decode(token_string, jwk, claims_options=claims_options)
            claims.validate()
        except (
            MissingClaimError,
            InvalidClaimError,
            InvalidTokenError,
            ExpiredTokenError,
        ) as e:
            raise NotAuthorizedException(detail=e.description)
        except Exception:
            raise NotAuthorizedException(detail="Invalid token")

        oid: str | None = claims.get("oid")
        user_ip: str | None = connection.client.host if connection.client else None

        if not oid:
            raise NotAuthorizedException(detail="Invalid token")

        vsc: str = connection.headers.get("x-vsc-version", "n/a")
        ext: str = connection.headers.get("x-ext-version", "n/a")

        return AuthenticationResult(
            user=dict(
                oid=oid,
                uip=user_ip,
                vsc=(vsc[:32] + "...") if len(vsc) > 32 else vsc,
                ext=(ext[:32] + "...") if len(ext) > 32 else ext,
            )
        )
