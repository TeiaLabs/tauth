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

from ..organizations import controllers as org_controllers
from ..schemas import Creator

log = getLogger(__name__)


class OktaSettings(BaseSettings):
    OKTA_DOMAIN: str = ""
    OKTA_AUDIENCE: str = ""

    def validate(self):
        return True

    class Config:
        env_file = ".env"


class ManyJSONKeyStore:
    sets = OktaSettings()
    domains: dict[str, tuple[str, str]] = {
        "/psg/chat/webui": (sets.OKTA_DOMAIN, sets.OKTA_AUDIENCE),
    }

    @classmethod
    @ttl_cache(maxsize=1, ttl=60 * 60 * 6)
    def get_jwk(cls, domain: str) -> KeySet:
        log.debug("Fetching JWK.")
        with Client() as client:
            res = client.get(f"https://{domain}/oauth2/v1/keys")
        try:
            res.raise_for_status()
        except HTTPError as e:
            log.error(f"Failed to fetch JWK from {domain}.")
            raise e
        log.info(f"JWK fetched from {domain}.")
        return JsonWebKey.import_key_set(res.json())


class RequestAuthenticator:
    settings = OktaSettings()

    @staticmethod
    def get_id_claims(domain: str) -> dict:
        id_claims_options = {
            "iss": {"essential": True, "value": f"https://{domain}"},
            "exp": {"essential": True},
        }
        return id_claims_options

    @staticmethod
    def get_access_claims(domain: str, audience: str) -> dict:
        access_claims_options = {
            "aud": {"essential": True, "value": audience},
            "exp": {"essential": True},
            "iss": {"essential": True, "value": f"https://{domain}"},
        }
        return access_claims_options

    @staticmethod
    def validate(request: Request, token_value: str, id_token: str):
        for i, (app_name, (domain, audience)) in enumerate(
            ManyJSONKeyStore.domains.items()
        ):
            print(app_name, domain, audience)
            j_w_k = ManyJSONKeyStore.get_jwk(domain)
            try:
                access_claims = jwt.decode(
                    token_value,
                    j_w_k,
                    claims_options=RequestAuthenticator.get_access_claims(
                        domain, f"https://{domain}"
                    ),
                )
                access_claims.validate()
            except (
                ExpiredTokenError,
                InvalidClaimError,
                InvalidTokenError,
                MissingClaimError,
            ) as e:
                if i == len(ManyJSONKeyStore.domains) - 1:
                    raise HTTPException(
                        401,
                        detail={
                            "loc": ["headers", "Authorization"],
                            "msg": e.description,
                            "type": e.error,
                        },
                    )
                continue
            except Exception as e:
                if i == len(ManyJSONKeyStore.domains) - 1:
                    raise HTTPException(
                        401,
                        detail={
                            "loc": ["headers", "Authorization"],
                            "msg": str(e),
                            "type": type(e).__name__,
                        },
                    )
                continue
            try:
                id_claims = jwt.decode(
                    id_token,
                    j_w_k,
                    claims_options=RequestAuthenticator.get_id_claims(domain),
                )
                id_claims.validate()
            except (
                MissingClaimError,
                InvalidClaimError,
                InvalidTokenError,
                ExpiredTokenError,
            ) as e:
                if i == len(ManyJSONKeyStore.domains) - 1:
                    raise HTTPException(
                        401,
                        detail={
                            "loc": ["headers", "X-ID-Token"],
                            "msg": e.description,
                            "type": e.error,
                        },
                    )
                continue
            except Exception as e:
                if i == len(ManyJSONKeyStore.domains) - 1:
                    raise HTTPException(
                        401,
                        detail={
                            "loc": ["headers", "X-ID-Token"],
                            "msg": str(e),
                            "type": type(e).__name__,
                        },
                    )
                continue
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
            # TODO: Okta deals with organizations using separate domains.
            # So I used the domain name in the `external_ids` field.
            org_id = domain
            org = org_controllers.read_one(
                external_id_key={"$regex": r"/.*--okta-org-id"},  # type: ignore
                external_id_value=org_id,
            )
            if not org:
                raise HTTPException(
                    401, detail=f"Organization with id '{org_id}' not found."
                )
            request.state.creator = Creator(
                client_name=org.name + app_name,
                token_name="okta-jwt",
                user_email=user_email,
            )
            # TODO: forward user IP using a header?
            if request.client is not None:
                request.state.creator.user_ip = request.client.host
            if request.headers.get("x-forwarded-for"):
                request.state.creator.user_ip = request.headers["x-forwarded-for"]
            return
