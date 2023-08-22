from httpx import Client
from starlite import (
    AbstractAuthenticationMiddleware,
    AuthenticationResult,
    NotAuthorizedException,
    ASGIConnection,
)
from authlib.jose import jwt  # type: ignore
from authlib.jose.rfc7517.jwk import (  # type: ignore
    JsonWebKey,
    KeySet,
)
from authlib.jose.errors import (  # type: ignore
    MissingClaimError,
    InvalidClaimError,
    ExpiredTokenError,
    InvalidTokenError,
)
from ..models.user import AuthenticatedUser
from ..settings import settings


def get_keys(domain: str) -> KeySet:
    with Client() as client:
        res = client.get(f"https://{domain}/.well-known/jwks.json")
        res.raise_for_status()
        return JsonWebKey.import_key_set(res.json())


jwk = get_keys(settings.AUTH0_DOMAIN)

authorization_claims_options = {
    "iss": {"essential": True, "value": f"https://{settings.AUTH0_DOMAIN}/"},
    "aud": {"essential": True, "value": settings.AUTH0_AUDIENCE},
    "exp": {"essential": True},
}

id_claims_options = {
    "iss": {"essential": True, "value": f"https://{settings.AUTH0_DOMAIN}/"},
    "exp": {"essential": True},
}


class AuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        authorization_header = connection.headers.get("Authorization")
        if not authorization_header:
            raise NotAuthorizedException()

        authorization_token_parts = authorization_header.split(None, 1)
        if len(authorization_token_parts) != 2:
            raise NotAuthorizedException()

        authorization_token_type, authorization_token_string = authorization_token_parts

        if authorization_token_type.lower() != "bearer":
            raise NotAuthorizedException()

        try:
            authorization_claims = jwt.decode(
                authorization_token_string, jwk, claims_options=authorization_claims_options
            )
            authorization_claims.validate()
        except (MissingClaimError, InvalidClaimError, InvalidTokenError, ExpiredTokenError) as e:
            raise NotAuthorizedException(detail=e.description)
        except Exception:
            raise NotAuthorizedException(detail="Invalid token")

        id_token_string = connection.headers.get("X-ID-Token")
        if not id_token_string:
            raise NotAuthorizedException()

        try:
            id_claims = jwt.decode(id_token_string, jwk, claims_options=id_claims_options)
            id_claims.validate()
        except (MissingClaimError, InvalidClaimError, InvalidTokenError, ExpiredTokenError) as e:
            raise NotAuthorizedException(detail=e.description)
        except Exception:
            raise NotAuthorizedException(detail="Invalid token")

        sub: str | None = id_claims.get("sub")
        eml: str | None = id_claims.get("email")
        uip: str | None = connection.client.host if connection.client else None

        if not sub or not eml:
            raise NotAuthorizedException(detail="Invalid token")

        vsc: str = connection.headers.get("x-vsc-version", "n/a")
        ext: str = connection.headers.get("x-ext-version", "n/a")

        return AuthenticationResult(
            user=AuthenticatedUser(
                sub=sub,
                eml=eml,
                uip=uip,
                vsc=(vsc[:32] + "...") if len(vsc) > 32 else vsc,
                ext=(ext[:32] + "...") if len(ext) > 32 else ext,
            )
        )
