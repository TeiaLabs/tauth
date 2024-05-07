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
from ..controllers import creation, reading
from ..entities.models import EntityDAO
from ..injections import privileges
from ..schemas import Creator

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
    logger.debug(
        f"Validating scoped access level: {creator.client_name!r} -> {client_in.name!r}."
    )
    validate_creation_access_level(client_in.name, creator.client_name)

    try:
        organization = f"/{client_in.name.split("/")[1]}"
        logger.debug(f"Checking if organization entity with handle {organization!r} exists.")
        filters = {"handle": organization, "type": "organization"}
        org = reading.read_one_filters(creator={}, model=EntityDAO, **filters)
    except HTTPException as e:
        details = RequestValidationError(
            loc=["body", "name"],
            msg="Cannot create client for non-existent organization entity.",
            type="DocumentNotFound",
        )
        raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail=details)
    
    # TODO: maybe automatically add the `melt-key` authprovider for org entity
    # if it does not have one.

    # TODO: so far, we do nothing about the scopes of a client beyond the
    # first check (i.e., root organization). Maybe we should create services
    # using the remaining scopes. One idea would be to join the scopes with
    # a "--" character to create a single child service entity.
    # Example: `/teialabs/athena/chat` -> `athena--chat`, child of entity
    # with handle `/teialabs`.

    try:
        token_name = "default"
        logger.debug("Creating {token_name!r} token.")
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
                type="DuplicateKeyError",  # TODO: check if this is correct
            )
        raise HTTPException(status_code=s.HTTP_409_CONFLICT, detail=details)

    out = ClientCreationOut(
        created_at=datetime.now(timezone.utc),
        created_by=creator,
        _id=org.id,  # TODO: I think this is the only thing that makes sense...
        name=client_in.name,
        tokens=[token_out],
        users=[],  # TODO: not sure what to do here... this list is probably always empty
    )
    return out


@router.get("", status_code=s.HTTP_200_OK)
@router.get("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_many(request: Request) -> list[ClientOut]:
    creator: Creator = request.state.creator
    logger.debug(f"Reading all authproviders for {creator.client_name!r}.")
    filters = {"type": "melt-key", "organization_ref.handle": {"$regex": f"^{creator.client_name}"}} 
    items = reading.read_many(creator={}, model=AuthProviderDAO, **filters)
    # TODO: to get all sub-clients, we would need to have registered all
    # sub-clients (scopes) as entities (services, perhaps).
    items = [
        ClientOut(
            created_at=i.created_at,
            created_by=i.created_by,
            _id=str(i.id),
            name=i.organization_ref.handle,
        )
        for i in items
    ]
    return items


@router.get("/{name:path}", status_code=s.HTTP_200_OK)
@router.get("/{name:path}/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def read_one(request: Request, name: str) -> ClientOutJoinTokensAndUsers:
    creator: Creator = request.state.creator
    logger.debug(f"Reading client {name!r}.")

    logger.debug(f"Validating scoped access level: {creator.client_name!r} -> {name!r}.")
    validate_scope_access_level(name, creator.client_name)

    logger.debug(f"Reading corresponding organization entity for client {creator.client_name!r}.")
    filters = {"type": "organization", "handle": creator.client_name}
    org = reading.read_one_filters(creator={}, model=EntityDAO, **filters) 

    logger.debug(f"Reading client tokens for entity {org.handle!r}.")
    tokens = reading.read_many(creator={}, model=TokenDAO, client_name=org.handle)
    tokens_view = [TokenMeta(**t.model_dump()) for t in tokens]

    logger.debug(f"Reading users for entity {org.handle!r}.")
    filters_user = {"type": "user", "owner_ref.handle": org.handle}
    users = reading.read_many(creator={}, model=EntityDAO, **filters_user)
    users = [UserOut(**u.model_dump(), email=u.handle) for u in users]

    client_view = ClientOutJoinTokensAndUsers(
        created_at=org.created_at,
        created_by=org.created_by,
        _id=org.id,
        name=org.handle,
        tokens=tokens_view,
        users=users,
    )
    return client_view
