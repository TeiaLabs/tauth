from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from pymongo.errors import DuplicateKeyError

from ..models import TokenDAO
from ..schemas import Creator, TokenCreationOut, TokenMeta
from ..settings import Settings
from ..utils import create_token


def create_one(client_name: str, creator: Creator, token_name: str) -> TokenCreationOut:
    token = TokenDAO(
        client_name=client_name,
        created_by=creator,
        name=token_name,
        value=create_token(client_name, token_name),
    )
    try:
        TokenDAO.collection(Settings.get().TAUTH_MONGODB_DBNAME).insert_one(
            token.bson()
        )
    except DuplicateKeyError as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg=f"Token names should be unique within a client (client_name={client_name!r}, name={token_name!r}).",
            type=e.__class__.__name__,
        )
        raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=details)
    creation_out = TokenCreationOut(**token.bson())
    return creation_out


def find_many(**kwargs) -> list[TokenMeta]:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    tokens = TokenDAO.collection(Settings.get().TAUTH_MONGODB_DBNAME).find(
        filter=filters
    )
    tokens_view = [TokenMeta(**token) for token in tokens]
    return tokens_view


def find_one(**kwargs) -> TokenMeta:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    token = TokenDAO.collection(Settings.get().TAUTH_MONGODB_DBNAME).find_one(
        filter=filters
    )
    if token is None:
        raise HTTPException(
            status_code=s.HTTP_404_NOT_FOUND,
            detail=f"Token not found with filters {filters!r}.",
        )
    token_view = TokenMeta(**token)
    return token_view
