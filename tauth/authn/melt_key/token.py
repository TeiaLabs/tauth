import re
import secrets
from functools import lru_cache

from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from multiformats import multibase

from ...settings import Settings
from ..melt_key.models import TokenDAO


def parse_token(token_value: str) -> tuple[str, str, str]:
    """
    Parse token string into client name, token name, and token value.

    Raise an error if token is incorrectly formatted.
    >>> parse_token("MELT_/client-name--token-name--abcdef123456789")
    ('client-name', 'token-name', 'abcdef123456789')
    """
    stripped = token_value.lstrip("MELT_")
    pieces = stripped.split("--")
    if len(pieces) != 3:
        code, m = 401, "Token is not in the correct format."
        raise HTTPException(status_code=code, detail=m)
    return tuple(pieces)  # type: ignore


def create_token(client_name: str, token_name: str):
    token_value = multibase.encode(secrets.token_bytes(24), "base58btc")
    fmt_token_value = f"MELT_{client_name}--{token_name}--{token_value}"
    return fmt_token_value


@lru_cache(maxsize=32)
def validate_token_against_db(token: str, client_name: str, token_name: str):
    filters = {"client_name": client_name, "name": token_name}
    entity = TokenDAO.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find_one(
        filter=filters
    )
    if not entity:
        d = {
            "filters": filters,
            "msg": f"Token does not exist for client.",
            "type": "DocumentNotFound",
        }
        raise HTTPException(status_code=s.HTTP_401_UNAUTHORIZED, detail=d)
    if not secrets.compare_digest(token, entity["value"]):
        code, m = s.HTTP_401_UNAUTHORIZED, "Token does not match."
        raise HTTPException(status_code=code, detail={"msg": m})
    return entity


def sanitize_client_name(client_name: str, loc: list[str] = ["body", "name"]) -> str:
    print(client_name)
    if client_name != "/":
        clean_client_name = client_name.rstrip("/").lower()
    else:
        clean_client_name = client_name
    if not clean_client_name.startswith("/"):
        details = RequestValidationError(
            loc=loc,
            msg="Client names are namespaced and must be absolute (start with a slash character).",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_422_UNPROCESSABLE_ENTITY, detail=details)
    if pos := re.search(r"\s", clean_client_name):
        details = RequestValidationError(
            loc=loc + [str(pos)],
            msg="Client name cannot contain spaces.",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_422_UNPROCESSABLE_ENTITY, detail=details)
    if pos := re.search(r"//", clean_client_name):
        details = RequestValidationError(
            loc=loc + [str(pos)],
            msg="Client name cannot contain consecutive slashes.",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_422_UNPROCESSABLE_ENTITY, detail=details)
    if pos := re.search(r"--", clean_client_name):
        details = RequestValidationError(
            loc=loc + [str(pos)],
            msg="Client name cannot contain consecutive dashes. Single dashes are fine.",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_422_UNPROCESSABLE_ENTITY, detail=details)
    return clean_client_name
