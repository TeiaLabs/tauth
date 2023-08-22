from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from redb.interface.errors import UniqueConstraintViolation

from ..settings import Settings
from ..models import TokenDAO
from ..schemas import Creator, TokenCreationOut, TokenMeta
from ..utils import create_token


def create_one(client_name: str, creator: Creator, token_name: str) -> TokenCreationOut:
    token = TokenDAO(
        client_name=client_name,
        created_by=creator,
        name=token_name,
        value=create_token(client_name, token_name),
    )
    try:
        TokenDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).insert_one(token)
    except UniqueConstraintViolation as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg=f"Token names should be unique within a client (client_name={client_name!r}, name={token_name!r}).",
            type=e.__class__.__name__,
        )
        raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=details)
    token_view = TokenCreationOut(**token.dict())
    return token_view


def find_many(**kwargs) -> list[TokenMeta]:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    tokens = TokenDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_many(filter=filters)
    tokens_view = [TokenMeta(**token.dict()) for token in tokens]
    return tokens_view


def find_one(**kwargs) -> TokenMeta:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    token = TokenDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_one(filter=filters)
    token_view = TokenMeta(**token.dict())
    return token_view
