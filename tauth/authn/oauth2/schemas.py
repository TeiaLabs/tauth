from typing import Self

from jwt import MissingRequiredClaimError
from pydantic import BaseModel

from ...authproviders.models import AuthProviderDAO


class OAuth2Settings(BaseModel):
    domain: str
    audience: str

    @classmethod
    def from_authprovider(cls, authprovider: AuthProviderDAO) -> Self:
        iss = authprovider.get_external_id("issuer")
        if not iss:
            raise MissingRequiredClaimError("iss")
        aud = authprovider.get_external_id("audience")
        if not aud:
            raise MissingRequiredClaimError("aud")
        return cls(domain=iss, audience=aud)
