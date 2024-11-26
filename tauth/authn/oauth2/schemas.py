from typing import Self

from jwt import MissingRequiredClaimError
from pydantic import BaseModel

from ...authproviders.models import AuthProviderDAO


class OAuth2Settings(BaseModel):
    domain: str
    audience: str
    userinfo_url: str
    jwks_url: str

    @classmethod
    def from_authprovider(cls, authprovider: AuthProviderDAO) -> Self:
        iss = authprovider.get_external_id("issuer")
        if not iss:
            raise MissingRequiredClaimError("iss")

        aud = authprovider.get_external_id("audience")
        if not aud:
            raise MissingRequiredClaimError("aud")

        if authprovider.type == "auth0":
            userinfo_url = f"{iss.rstrip("/")}/userinfo"
            jwks_url = f"{iss.rstrip("/")}/.well-known/jwks.json"
        elif authprovider.type == "okta":
            userinfo_url = f"{iss.rstrip("/")}/oauth2/v1/userinfo"
            jwks_url = f"{iss.rstrip("/")}/oauth2/v1/keys"
        else:
            raise ValueError(f"Unknown OAuth2 provider type: {type!r}.")

        return cls(
            domain=iss,
            audience=aud,
            userinfo_url=userinfo_url,
            jwks_url=jwks_url,
        )
