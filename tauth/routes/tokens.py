from fastapi import APIRouter, Body, HTTPException, Path, Request
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from redb.interface.errors import DocumentNotFound

from ..controllers import client as client_controller
from ..controllers import tokens as token_controller
from ..models import TokenDAO
from ..schemas import Creator, TokenCreationOut
from ..utils.access_helper import sanitize_client_name

router = APIRouter(prefix="/clients")


@router.post("/{client_name:path}/tokens", status_code=s.HTTP_201_CREATED)
async def create_one(
    request: Request, client_name: str = Path(), name: str = Body(..., embed=True)
) -> TokenCreationOut:
    """
    Create a token.

    Clients can create tokens for themselves and their subclients, but not for parent clients.
    """
    creator: Creator = request.state.creator
    try:
        client_controller.read_one(name=client_name)
    except DocumentNotFound as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot create token for non-existent client.",
            type=e.__class__.__name__,
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)
    clean_client_name = sanitize_client_name(client_name, loc=["path", "client_name"])
    # allow / to create tokens in /client and /client/subclient, but not the opposite.
    if clean_client_name.find(creator.client_name) != 0:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg=f"Cannot create token for {clean_client_name!r} which lies outside or above your access level ({creator.client_name!r}).",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=details)
    token = token_controller.create_one(client_name, creator=creator, token_name=name)
    return token


@router.delete(
    "/{client_name:path}/tokens/{token_name}", status_code=s.HTTP_204_NO_CONTENT
)
async def delete_one(
    request: Request, client_name: str = Path(), token_name: str = Path()
):
    """
    Delete a token.

    Clients can delete tokens for themselves and their subclients, but not for parent clients.
    """
    creator: Creator = request.state.creator
    try:
        client_controller.read_one(name=client_name)
    except DocumentNotFound as e:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg="Cannot delete token for non-existent client.",
            type=e.__class__.__name__,
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)
    clean_client_name = sanitize_client_name(client_name, loc=["path", "client_name"])
    # allow / to delete tokens in /client and /client/subclient, but not the opposite.
    if clean_client_name.find(creator.client_name) != 0:
        details = RequestValidationError(
            loc=["path", "client_name"],
            msg=f"Cannot delete token for {clean_client_name!r} which lies outside or above your access level ({creator.client_name!r}).",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=details)
    # TODO: needs soft delete.
    TokenDAO.delete_one(filter=dict(client_name=client_name, name=token_name))
