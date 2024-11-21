from typing import Any

import jwt as pyjwt
from cachetools.func import ttl_cache
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from fastapi import HTTPException
from fastapi import status as s
from httpx import Client, HTTPError
from jwt import PyJWKClient, PyJWKSet
from loguru import logger

from ...entities.models import EntityDAO
from ...entities.schemas import EntityIntermediate
from ...schemas.infostar import Infostar
from ...utils import creation, reading


class ManyJSONKeySetStore:
    @classmethod
    @ttl_cache(maxsize=32, ttl=60 * 60 * 6)
    def get_jwks(cls, type: str, domain: str) -> PyJWKSet:
        logger.debug(f"Fetching JWKS for {type!r} OAuth2 provider from {domain!r}.")
        # Clean up the domain
        domain = domain.strip("/")
        if type == "auth0":
            final_domain = f"{domain}/.well-known/jwks.json"
        elif type == "okta":
            final_domain = f"{domain}/oauth2/v1/keys"
        else:
            raise ValueError(f"Unknown OAuth2 provider type: {type!r}.")
        with Client() as client:
            logger.debug(f"Fetching JWKS from {final_domain}.")
            res = client.get(final_domain)
        try:
            res.raise_for_status()
        except HTTPError as e:
            logger.error(f"Failed to fetch JWKS from {domain}.")
            raise e

        return PyJWKSet.from_dict(res.json())


def get_token_headers(token: str) -> dict[str, Any]:
    header = pyjwt.get_unverified_header(token)
    return header


def get_token_unverified_claims(token: str) -> dict[str, Any]:
    claims = pyjwt.decode(token, options={"verify_signature": False})
    return claims


def get_signing_key(kid: str, domain: str, type: str) -> str | None:
    jwk_set = ManyJSONKeySetStore.get_jwks(type, domain)
    signing_key = PyJWKClient.match_kid(jwk_set.keys, kid)
    if isinstance(signing_key, RSAPrivateKey):
        return signing_key.key.public_key()
    return signing_key.key if signing_key else None


def register_user(
    user_email: str,
    auth_provider_org_ref: dict[str, str],
    infostar: Infostar,
):
    try:
        filters = {
            "type": "user",
            "handle": user_email,
            "owner_ref.handle": auth_provider_org_ref["handle"],
        }
        reading.read_one_filters(infostar=infostar, model=EntityDAO, **filters)
    except HTTPException as e:
        if e.status_code in (s.HTTP_404_NOT_FOUND, s.HTTP_409_CONFLICT):
            user_i = EntityIntermediate(
                handle=user_email,
                owner_ref=auth_provider_org_ref,  # type: ignore
                type="user",
            )
            creation.create_one(user_i, EntityDAO, infostar=infostar)
        else:
            logger.error(e)
            raise e