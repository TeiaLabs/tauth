from fastapi import APIRouter, Body, HTTPException, Path, Request
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from loguru import logger

from ..auth.melt_key.authorization import validate_scope_access_level
from ..auth.melt_key.models import TokenDAO
from ..auth.melt_key.schemas import TokenCreationIntermediate, TokenCreationOut
from ..auth.melt_key.token import create_token
from ..authproviders.models import AuthProviderDAO
from ..controllers import creation, reading
from ..entities.models import EntityDAO
from ..schemas.creator import Creator

router = APIRouter(prefix="/clients", tags=["legacy"])


@router.post("/{client_name:path}/tokens", status_code=s.HTTP_201_CREATED)
async def create_one(
    request: Request,
    client_name: str = Path(),
    name: str = Body(..., embed=True),
) -> TokenCreationOut:
    """
    Create a token.

    Clients can create tokens for themselves and their subclients, but not for parent clients.
    """
    logger.debug(f"Attempting to CREATE token {name!r} for {client_name!r}.")
    creator: Creator = request.state.creator
    try:
        organization = f"/{client_name.split("/")[1]}"
        logger.debug(f"Checking if organization entity with handle {organization!r} exists.")
        filters = {"handle": organization, "type": "organization"}
        org = reading.read_one_filters(creator={}, model=EntityDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot create token for non-existent organization entity.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    try:
        logger.debug(f"Checking if organization {org.handle!r} has 'melt-key' authprovider.")
        provider_filters = {"type": "melt-key", "organization_ref.handle": org.handle}
        melt_key_authprovider = reading.read_one_filters(
            creator={}, model=AuthProviderDAO, **provider_filters
        )
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot create token for organization without 'melt-key' authprovider.",
            type="DocumentNotFound",  # TODO: other error type here?
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    logger.debug(f"Validating scoped access level: {creator.client_name!r} -> {client_name!r}.")
    validate_scope_access_level(client_name, creator.client_name)

    logger.debug("Creating token.")
    token = TokenCreationIntermediate(
        client_name=client_name,
        name=name,
        value=create_token(client_name, name),
    )
    token = creation.create_one(token, model=TokenDAO, creator=creator)
    token_out = TokenCreationOut(**token.model_dump())
    return token_out


@router.delete(
    "/{client_name:path}/tokens/{token_name}", status_code=s.HTTP_204_NO_CONTENT
)
async def delete_one(
    request: Request,
    client_name: str = Path(),
    token_name: str = Path(),
):
    """
    Delete a token.

    Clients can delete tokens for themselves and their subclients, but not for parent clients.
    """
    logger.debug(f"Attempting to DELETE token {token_name!r} for {client_name!r}.")
    creator: Creator = request.state.creator
    try:
        organization = f"/{client_name.split("/")[1]}"
        logger.debug(f"Checking if organization entity with handle {organization!r} exists.")
        filters = {"handle": organization, "type": "organization"}
        reading.read_one_filters(creator={}, model=EntityDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot delete token for non-existent organization entity.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    logger.debug(f"Validating scoped access level: {creator.client_name!r} -> {client_name!r}.")
    validate_scope_access_level(client_name, creator.client_name)

    logger.debug("Deleting token.")
    # TODO: needs soft delete.
    TokenDAO.collection().delete_one(
        filter=dict(client_name=client_name, name=token_name)
    )
