from fastapi import HTTPException
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from redb.interface.errors import DocumentNotFound

from ..models import ClientDAO
from ..schemas import ClientCreation, ClientOut, ClientOutJoinTokensAndUsers, Creator
from ..settings import Settings
from . import tokens, users


def create_one(client_in: ClientCreation, creator: Creator) -> ClientDAO:
    client = ClientDAO(name=client_in.name, created_by=creator)
    ClientDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).insert_one(client)
    return client


def read_many(**kwargs) -> list[ClientOut]:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    clients = ClientDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_many(
        filter=filters
    )
    clients_view = [ClientOut(**client.dict()) for client in clients]
    return clients_view


def read_one(**kwargs) -> ClientOutJoinTokensAndUsers:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    try:
        client = ClientDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_one(
            filter=filters
        )
    except DocumentNotFound as e:
        details = RequestValidationError(
            loc=["path", "name"],
            msg=f"Client not found with filters={filters}.",
            type=e.__class__.__name__,
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)
    client_view = ClientOutJoinTokensAndUsers(
        **client.dict(),
        tokens=tokens.find_many(client_name=client.name),
        users=users.read_many(client_name=client.name),
    )
    return client_view
