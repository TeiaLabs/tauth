import re

from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError


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


def sanitize_client_name(client_name: str, loc: list[str] = ["body", "name"]) -> str:
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
