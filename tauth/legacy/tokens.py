from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from loguru import logger

from ..authn.melt_key.authorization import validate_scope_access_level
from ..authn.melt_key.models import TokenDAO
from ..authn.melt_key.schemas import TokenCreationIntermediate, TokenCreationOut
from ..authn.melt_key.token import create_token
from ..authproviders.models import AuthProviderDAO
from ..authz import privileges
from ..entities.models import EntityDAO
from ..schemas import Creator, Infostar
from ..settings import Settings
from ..utils import creation, reading
from .schemas import MeltAPIKeyIn

router = APIRouter(prefix="/keys", tags=["legacy"])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    body: MeltAPIKeyIn,
    infostar: Infostar = Depends(privileges.is_valid_user),
) -> TokenCreationOut:
    """
    Create a token.

    Clients can create tokens for themselves and their subclients, but not for parent clients.
    """
    creator: Creator = request.state.creator
    logger.debug(
        f"Attempting to create token {body.name!r} for {body.organization_handle!r}."
    )
    try:
        logger.debug(
            f"Checking if organization entity {body.organization_handle!r} exists."
        )
        filters = {"handle": body.organization_handle, "type": "organization"}
        org = reading.read_one_filters(infostar, model=EntityDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot create token for non-existent organization entity.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    try:
        logger.debug(f"Checking if org {org.handle!r} has 'melt-key' authprovider.")
        filters = {"type": "melt-key", "organization_ref.handle": org.handle}
        _ = reading.read_one_filters(infostar, model=AuthProviderDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot create token for organization with no 'melt-key' authprovider.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    logger.debug(
        f"Validating access: {infostar.authprovider_org!r} -> {body.organization_handle!r}."
    )
    validate_scope_access_level(body.organization_handle, infostar.authprovider_org)

    try:
        logger.debug(f"Creating {body.name!r} token.")
        token = TokenCreationIntermediate(
            client_name=creator.client_name,
            name=body.name,
            value=create_token(creator.client_name, body.name),
        )
        token = creation.create_one(token, model=TokenDAO, infostar=infostar)
        token_out = TokenCreationOut(
            **token.model_dump(exclude={"created_by"}),
            created_by=infostar,
        )
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "name"],
            msg=f"Token {body.name!r} already exists.",
            type="DuplicateKeyError",
        )
        raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=details)

    return token_out


@router.delete(
    "/{client_name:path}/tokens/{token_name}", status_code=s.HTTP_204_NO_CONTENT
)
async def delete_one(
    request: Request,
    client_name: str = Path(),
    token_name: str = Path(),
    infostar: Infostar = Depends(privileges.is_valid_admin),
):
    """
    Delete a token.

    Clients can delete tokens for themselves and their subclients, but not for parent clients.
    """
    creator: Creator = request.state.creator
    logger.debug(f"Attempting to DELETE token {token_name!r} for {client_name!r}.")
    creator: Creator = request.state.creator
    try:
        org_handle = client_name.split("/")[1]
        organization = f"/{org_handle}"
        logger.debug(f"Checking if organization entity {organization!r} exists.")
        filters = {"handle": organization, "type": "organization"}
        reading.read_one_filters(infostar, model=EntityDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot delete token for non-existent organization entity.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    logger.debug(f"Validating access: {creator.client_name!r} -> {client_name!r}.")
    validate_scope_access_level(client_name, creator.client_name)

    filters = {"client_name": client_name, "name": token_name}
    try:
        reading.read_one_filters(infostar, model=TokenDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["path", "token_name"],
            msg=f"Token {token_name!r} does not exist.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    logger.debug("Deleting token.")
    # TODO: needs soft delete.
    TokenDAO.collection(alias=Settings.get().REDBABY_ALIAS).delete_one(filters)
