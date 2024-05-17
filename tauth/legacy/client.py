from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi import status as s
from http_error_schemas.schemas import RequestValidationError
from loguru import logger

from ..auth.melt_key.authorization import (
    validate_creation_access_level,
    validate_scope_access_level,
)
from ..auth.melt_key.models import TokenDAO
from ..auth.melt_key.schemas import (
    ClientCreation,
    ClientCreationOut,
    ClientOut,
    ClientOutJoinTokensAndUsers,
    TokenCreationIntermediate,
    TokenCreationOut,
    TokenMeta,
    UserOut,
)
from ..auth.melt_key.token import create_token
from ..authproviders.models import AuthProviderDAO
from ..entities.models import EntityDAO
from ..injections import privileges
from ..schemas import Creator
from ..settings import Settings
from ..utils import creation, reading
from . import users as users_controller

router = APIRouter(prefix="/clients", tags=["legacy"])


@router.post("", status_code=s.HTTP_201_CREATED)
@router.post("/", status_code=s.HTTP_201_CREATED, include_in_schema=False)
async def create_one(
    request: Request,
    client_in: ClientCreation = Body(),
    creator: Creator = Depends(privileges.is_valid_admin),
) -> ClientCreationOut:
    """
    Create a new client.

    - A client with name `/teia/athena` can only be created by `/teia` or `/`.
    - In order to create `/teia/athena/chat`, you must first create `/teia/athena`.
    - Trailing slashes are ignored.
    """
    logger.debug(f"Creating a new client: {client_in.name!r}.")
    logger.debug(f"Validating access: {creator.client_name!r} -> {client_in.name!r}.")
    validate_creation_access_level(client_in.name, creator.client_name)

    try:
        org_handle = client_in.name.split("/")[1]
        organization = f"/{org_handle}"
        logger.debug(f"Checking if organization entity {organization!r} exists.")
        filters = {"handle": organization, "type": "organization"}
        org = reading.read_one_filters(creator={}, model=EntityDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg="Cannot create client for non-existent organization entity.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    try:
        logger.debug(f"Checking if org {org.handle!r} has 'melt-key' authprovider.")
        filters = {"type": "melt-key", "organization_ref.handle": org.handle}
        provider = reading.read_one_filters(
            creator={},
            model=AuthProviderDAO,
            **filters,
        )
    except HTTPException as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg="Cannot create client for organization with no 'melt-key' authprovider.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    logger.debug(f"Checking if authprovider has necessary subclients.")
    existing_clients = set(
        sorted([e.value for e in provider.extra if e.name == "melt_key_client"])
    )
    logger.debug(f"Existing clients for authprovider: {existing_clients!r}.")
    needed_clients = [c for c in client_in.name.split("/")[:-1] if c != ""]
    needed_clients = [
        "/" + "/".join(needed_clients[: i + 1]) for i, _ in enumerate(needed_clients)
    ]
    logger.debug(f"Needed clients to create new client: {needed_clients!r}.")
    missing_clients = set(needed_clients) - existing_clients
    if missing_clients:
        details = RequestValidationError(
            loc=["body", "name"],
            msg=f"Cannot create client due to non-existent parent client(s): {missing_clients!r}.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)

    try:
        token_name = "default"
        logger.debug(f"Creating {token_name!r} token.")
        token = TokenCreationIntermediate(
            client_name=client_in.name,
            name=token_name,
            value=create_token(client_in.name, token_name),
        )
        token = creation.create_one(token, model=TokenDAO, creator=creator)
        token_out = TokenCreationOut(**token.model_dump())
    except HTTPException as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg="Client already exists.",
            type="DuplicateKeyError",
        )
        raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=details)

    logger.debug(f"Adding new subclient to authprovider.")
    authprovider_collection = AuthProviderDAO.collection(
        alias=Settings.get().TAUTH_REDBABY_ALIAS
    )
    authprovider_collection.update_one(
        filter={"_id": provider.id},
        update={
            "$push": {
                "extra": {
                    "name": "melt_key_client",
                    "value": client_in.name,
                }
            }
        },
    )

    out = ClientCreationOut(
        created_at=datetime.now(timezone.utc),
        created_by=creator,
        _id=org.id,
        name=client_in.name,
        tokens=[token_out],
        users=[],
    )
    return out


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(request: Request) -> list[ClientOut]:
    creator: Creator = request.state.creator
    logger.debug(f"Fetching clients for client: {creator.client_name!r}.")

    org_handle = creator.client_name.split("/")[1]
    organization = f"/{org_handle}"
    logger.debug(f"Organization entity handle: {organization!r}.")

    # Root token has access to multiple authproviders
    logger.debug(f"Reading 'melt-key' authprovider(s) for {creator.client_name!r}.")
    filters = {
        "type": "melt-key",
        "organization_ref.handle": {"$regex": f"^{organization}"},
    }
    providers = reading.read_many(creator={}, model=AuthProviderDAO, **filters)

    logger.debug(f"Finding all clients for authprovider(s).")
    clients = []
    for provider in providers:
        for e in provider.extra:
            if e.name == "melt_key_client":
                # We need to filter the clients depending on the subclient level
                if creator.client_name not in e.value:
                    continue
                clients.append(
                    ClientOut(
                        created_at=provider.created_at,
                        created_by=provider.created_by,
                        _id=str(provider.id),
                        name=e.value,
                    )
                )

    return clients


@router.get("/{name:path}", status_code=s.HTTP_200_OK)
@router.get("/{name:path}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(request: Request, name: str) -> ClientOutJoinTokensAndUsers:
    creator: Creator = request.state.creator
    logger.debug(f"Reading client {name!r}.")

    logger.debug(f"Validating access: {creator.client_name!r} -> {name!r}.")
    validate_scope_access_level(name, creator.client_name)
    # check if extra.key == melt_key_client has extra.value == name
    reading.read_one_filters(
        creator=creator,
        model=AuthProviderDAO,
        type="melt-key",
        **{
            "extra.name": "melt_key_client",
            "extra.value": name,
        },
    )
    logger.debug(f"Reading tokens for client {name!r}.")
    tokens: list[TokenDAO] = reading.read_many(
        creator={}, model=TokenDAO, client_name=name
    )
    tokens_view = [TokenMeta(**t.model_dump()) for t in tokens]

    org_handle = name.split("/")[1]
    organization = f"/{org_handle}"
    logger.debug(f"Reading organization entity: {organization!r}.")
    filters = {"type": "organization", "handle": organization}
    org = reading.read_one_filters(creator={}, model=EntityDAO, **filters)

    logger.debug(f"Reading users for organization entity {org.handle!r}.")
    users = await users_controller.read_many(request, org.handle, creator)

    client_view = ClientOutJoinTokensAndUsers(
        created_at=org.created_at,
        created_by=org.created_by,
        _id=org.id,  # TODO: Maybe this should be the authprovider ID
        name=name,
        tokens=tokens_view,
        users=users,
    )
    return client_view
