import secrets

from fastapi import HTTPException
from multiformats import multibase


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
    return tuple(pieces)


def create_token(client_name: str, token_name: str):
    token_value = multibase.encode(secrets.token_bytes(24), "base58btc")
    fmt_token_value = f"MELT_{client_name}--{token_name}--{token_value}"
    return fmt_token_value
