import contextlib
import secrets
from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks, HTTPException, Request
from fastapi import status as s
from loguru import logger
from pydantic import validate_email
from pymongo.errors import BulkWriteError
from redbaby.pyobjectid import PyObjectId

from ...entities.models import EntityDAO
from ...entities.schemas import EntityRef
from ...schemas import Creator, Infostar
from ...schemas.attribute import Attribute
from ...settings import Settings
from ..utils import SizedCache
from .token import parse_token, sanitize_client_name, validate_token_against_db

EmailStr = str


class RequestAuthenticator:
    CACHE: SizedCache[str, tuple[Creator, Infostar]] = SizedCache(max_size=512)

    @classmethod
    def validate(
        cls,
        request: Request,
        user_email: str | None,
        api_key_header: str,
        background_tasks: BackgroundTasks,
    ):
        key = f"user_email={user_email}&api_key_header={api_key_header}"
        cache_result = cls.CACHE.get(key)
        if cache_result:
            creator, infostar = cache_result
        else:
            creator, token_creator_user_email = cls.get_request_creator(
                token=api_key_header,
                user_email=user_email,
            )
            infostar = cls.get_request_infostar(creator)
            update_callback = cls.verify_user_on_db(
                creator=creator,
                infostar=infostar,
                token_creator_email=token_creator_user_email,
            )
            background_tasks.add_task(update_callback)
            cls.CACHE[key] = (creator, infostar)

        if request.headers.get("x-forwarded-for"):
            creator.user_ip = request.headers["x-forwarded-for"]
        elif request.client is not None:
            creator.user_ip = request.client.host

        request.state.creator = creator
        request.state.infostar = infostar

    @staticmethod
    def get_token_details(token_value: str) -> tuple[str, str, str]:
        """Returns the client and token name from the token value."""
        logger.debug("Parsing token to extract details.")
        client, name, value = parse_token(token_value)
        client = sanitize_client_name(client)
        logger.debug(f"client_name: {client!r}, token_name: {name!r}")
        return client, name, value

    @staticmethod
    def get_request_infostar(creator: Creator):
        logger.debug("Assembling Infostar based on Creator.")
        breadcrumbs = creator.client_name.split("/")
        owner_handle = f"/{breadcrumbs[1]}"
        service_handle = "--".join(breadcrumbs[2:]) if len(breadcrumbs) > 2 else ""
        infostar = Infostar(
            request_id=PyObjectId(),
            apikey_name=creator.token_name,
            authprovider_type="melt-key",
            authprovider_org=owner_handle,
            # extra=InfostarExtra(
            #     geolocation=request.headers.get("x-geo-location"),
            #     jwt_sub=request.headers.get("x-jwt-sub"),
            #     os=request.headers.get("x-os"),
            #     url=request.headers.get("x-url"),
            #     user_agent=request.headers.get("user-agent"),
            # ),
            extra={},
            original=None,
            service_handle=service_handle,
            user_handle=creator.user_email,
            user_owner_handle=owner_handle,
            client_ip=creator.user_ip,
        )
        return infostar

    @classmethod
    def get_request_creator(
        cls, token: str, user_email: str | None
    ) -> tuple[Creator, EmailStr | None]:
        """Returns the Creator and token creator user email for a given request."""
        if user_email is not None:
            try:
                validate_email(user_email)
            except:
                code, m = s.HTTP_401_UNAUTHORIZED, "User email is not valid."
                raise HTTPException(status_code=code, detail=m)

        logger.debug("Getting Creator for request.")
        client_name, token_name, token_value = cls.get_token_details(token)
        token_creator_user_email = None
        if client_name == "/":
            logger.debug("Using root token, checking email.")
            if user_email is None:
                code, m = (
                    s.HTTP_401_UNAUTHORIZED,
                    "User email is required for root client.",
                )
                raise HTTPException(status_code=code, detail=m)
            if not secrets.compare_digest(token, Settings.get().ROOT_API_KEY):
                print(token_value, Settings.get().ROOT_API_KEY)
                code, m = (
                    s.HTTP_401_UNAUTHORIZED,
                    "Root token does not match env var.",
                )
                raise HTTPException(status_code=code, detail=m)

            request_creator_user_email = user_email
        else:
            logger.debug("Using non-root token, validating token in DB.")
            token_obj = validate_token_against_db(token, client_name, token_name)
            token_creator_user_email = token_obj["created_by"]["user_handle"]
            if user_email is None:
                request_creator_user_email = token_obj["created_by"]["user_handle"]
            else:
                request_creator_user_email = user_email

        creator = Creator(
            client_name=client_name,
            token_name=token_name,
            user_email=request_creator_user_email,
        )
        return creator, token_creator_user_email

    @classmethod
    def verify_user_on_db(
        cls,
        creator: Creator,
        infostar: Infostar,
        token_creator_email: EmailStr | None,
    ) -> Callable[[], None]:
        logger.debug("Registering user.")
        melt_key_client_extra = Attribute(
            name="melt_key_client", value=creator.client_name
        )
        user_creator_email = (
            creator.user_email if token_creator_email is None else token_creator_email
        )

        if creator.client_name == "/":
            org_in = EntityDAO(
                handle="/",
                type="organization",
                created_by=infostar,
            )
            user_in = EntityDAO(
                handle=creator.user_email,
                type="user",
                extra=[melt_key_client_extra],
                created_by=infostar,
                owner_ref=EntityRef(
                    handle=org_in.handle,
                    type="organization",
                    owner_handle=None
                ),
            )
            collection = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
            with contextlib.suppress(BulkWriteError):
                collection.insert_many(
                    [org_in.bson(), user_in.bson()],
                    ordered=False,
                )

        authprovider_match: dict[str, Any] = {
            "authprovider.type": "melt-key",
        }
        if infostar.service_handle:
            authprovider_match["service_ref.handle"] = (infostar.service_handle,)

        org_handle = creator.client_name.split("/")[1]
        pipeline = [
            {"$match": {"type": "organization", "handle": f"/{org_handle}"}},
            {
                "$lookup": {
                    "from": "authproviders",
                    "localField": "handle",
                    "foreignField": "organization_ref.handle",
                    "as": "authprovider",
                }
            },
            {"$unwind": "$authprovider"},
            {"$match": authprovider_match},
            {
                "$lookup": {
                    "from": "entities",
                    "localField": "handle",
                    "foreignField": "owner_ref.handle",
                    "as": "user",
                }
            },
            {"$unwind": "$user"},
        ]

        collection = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
        if user_creator_email:
            pipeline.append(
                {
                    "$match": {
                        "user.type": "user",
                        "user.handle": user_creator_email,
                    }
                }
            )
            results = list(collection.aggregate(pipeline))
            if not results:
                d = {
                    "error": "DocumentNotFound",
                    "msg": f"Document with org_handle=/{org_handle} and user_handle={user_creator_email} not found. User or Authprovider no registered in organization.",
                }
                raise HTTPException(status_code=404, detail=d)
            if len(results) > 1:
                d = {
                    "error": "DocumentNotUnique",
                    "msg": f"Document with org_handle=/{org_handle} and user_handle={user_creator_email} is not unique.",
                }
                raise HTTPException(status_code=409, detail=d)
        else:
            pipeline.append({"$match": {"user.type": "user"}})
            results = list(collection.aggregate(pipeline))
            if not results:
                d = {
                    "error": "DocumentNotFound",
                    "msg": f"Document with org_handle=/{org_handle} not found. Users or Authprovider no registered in organization.",
                }
                raise HTTPException(status_code=404, detail=d)
            if len(results) > 1:
                d = {
                    "error": "DocumentNotUnique",
                    "msg": f"Document with org_handle=/{org_handle} is not unique. Please provide an e-mail to filter results.",
                }
                raise HTTPException(status_code=409, detail=d)

        data = results[0]
        data.pop("authprovider")
        user = data.pop("user")

        def callback():
            logger.debug(f"Adding {creator.client_name!r} client info.")
            entity_coll = EntityDAO.collection(alias=Settings.get().REDBABY_ALIAS)
            entity_coll.update_one(
                filter={"_id": user["_id"]},
                update={"$addToSet": {"extra": melt_key_client_extra.model_dump()}},
            )

        return callback
