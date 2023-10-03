from fastapi import APIRouter, Body, HTTPException, Request, Depends
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError

from ..controllers import client as client_controller
from ..controllers import tokens as token_controller
from ..controllers import users as user_controller
from ..schemas import (
    ClientCreation,
    ClientCreationOut,
    ClientOut,
    ClientOutJoinTokensAndUsers,
    Creator,
)
from ..injections import privileges
from ..utils import validate_creation_access_level

router = APIRouter(prefix="/clients")


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    client_in: ClientCreation = Body(),
    creator: Creator = Depends(privileges.is_valid_admin)
) -> ClientCreationOut:
    """
    Create a new client.

    - A client with name `/teia/athena` can only be created by `/teia` or `/`.
    - In order to create `/teia/athena/chat`, you must first create `/teia/athena`.
    - Trailing slashes are ignored.
    """
    validate_creation_access_level(client_in.name, creator.client_name)
    client = client_controller.create_one(client_in=client_in, creator=creator)
    token = token_controller.create_one(
        client_name=client_in.name, creator=creator, token_name="default"
    )
    client_users = user_controller.read_many(client_name=client.name)
    out = ClientCreationOut(
        **client.dict(),
        tokens=[token],
        users=client_users,
    )
    return out


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(request: Request) -> list[ClientOut]:
    creator: Creator = request.state.creator
    items = client_controller.read_many(name={"$regex": f"^{creator.client_name}"})
    return items


@router.get("/{name:path}", status_code=s.HTTP_200_OK)
@router.get("/{name:path}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(request: Request, name: str) -> ClientOutJoinTokensAndUsers:
    creator: Creator = request.state.creator
    if name.find(creator.client_name) != 0:
        details = RequestValidationError(
            loc=["path", "name"],
            msg=f"Cannot read client {name!r} which lies outside or above your access level ({creator.client_name!r}).",
            type="InvalidClientName",
        )
        raise HTTPException(status_code=s.HTTP_403_FORBIDDEN, detail=details)
    item = client_controller.read_one(name=name)
    return item
