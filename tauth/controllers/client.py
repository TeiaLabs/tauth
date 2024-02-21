from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from pymongo.errors import DuplicateKeyError

from ..models import ClientDAO
from ..schemas import ClientCreation, ClientOut, ClientOutJoinTokensAndUsers, Creator
from ..settings import Settings
from . import tokens, users


def create_one(client_in: ClientCreation, creator: Creator) -> ClientDAO:
    client = ClientDAO(name=client_in.name, created_by=creator)
    try:
        ClientDAO.collection(Settings.get().TAUTH_MONGODB_DBNAME).insert_one(
            client.bson()
        )
    except DuplicateKeyError as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg=f"Client names should be unique (name={client_in.name!r}).",
            type=e.__class__.__name__,
        )
        raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=details)
    return client


def read_many(**kwargs) -> list[ClientOut]:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    clients = ClientDAO.collection(Settings.get().TAUTH_MONGODB_DBNAME).find(
        filter=filters
    )
    clients_view = [ClientOut(**client) for client in clients]
    return clients_view


def read_one(**kwargs) -> ClientOutJoinTokensAndUsers:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    client = ClientDAO.collection(Settings.get().TAUTH_MONGODB_DBNAME).find_one(
        filter=filters
    )
    if client is None:
        details = RequestValidationError(
            loc=["path", "name"],
            msg=f"Client not found with filters={filters}.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)
    client_view = ClientOutJoinTokensAndUsers(
        **client,
        tokens=tokens.find_many(client_name=client["name"]),
        users=users.read_many(client_name=client["name"]),
    )
    return client_view
