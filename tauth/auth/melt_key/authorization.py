from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError

from .token import sanitize_client_name


def validate_creation_access_level(client_name: str, creator_client_name: str):
    """
    Validate if `client_name` is a direct child of `creator_client_name`.

    >>> validate_creation_access_level("/teia/athena/", "/teia")
    None
    >>> validate_creation_access_level("/teia", "/")
    None
    >>> validate_creation_access_level("/teia", "/osf")
    fastapi.exceptions.HTTPException: 403 Forbidden
    >>> validate_creation_access_level("/teia/athena", "/")
    fastapi.exceptions.HTTPException: 403 Forbidden
    """
    clean_client_name = sanitize_client_name(client_name)
    parent_name = clean_client_name.rsplit("/", 1)[0]
    if parent_name == "":
        parent_name = "/"
    if parent_name != creator_client_name:
        m = f"Client {creator_client_name!r} cannot create client {client_name!r}."
        raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=m)


def validate_scope_access_level(client_name: str, creator_client_name: str):
    clean_client_name = sanitize_client_name(client_name, loc=["path", "client_name"])
    # Allow / to operate in /client and /client/subclient, but not the opposite
    if clean_client_name.find(creator_client_name) != 0:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg=f"Cannot operate on token {clean_client_name!r} which lies outside or above your access level ({creator_client_name!r}).",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=details)
