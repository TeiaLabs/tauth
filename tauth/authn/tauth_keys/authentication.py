from fastapi import HTTPException, Request
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from ...entities.models import EntityDAO
from ...schemas import Creator, Infostar
from ...settings import Settings
from ..utils import SizedCache, get_request_ip
from .keygen import hash_value
from .models import TauthTokenDAO
from .utils import parse_key

EmailStr = str


class RequestAuthenticator:
    CACHE: SizedCache[str, tuple[Creator, Infostar]] = SizedCache(max_size=512)

    @classmethod
    def validate(
        cls,
        request: Request,
        api_key_header: str,
        impersonate_handle: str | None,
        impersonate_owner_handle: str | None,
    ):
        if api_key_header in cls.CACHE and impersonate_handle is None:
            creator, infostar = cls.CACHE[api_key_header]

        else:
            db_id, secret = parse_key(api_key_header)
            token_obj = cls.find_one_token(db_id)

            cls.validate_token(token_obj, secret)

            if impersonate_handle is not None and cls.can_impersonate(
                token_obj
            ):
                logger.info(
                    f"Impersonating {impersonate_handle} on behalf of {token_obj.entity.handle}"
                )
                entity = EntityDAO.from_handle(
                    handle=impersonate_handle,
                    owner_handle=impersonate_owner_handle,
                )
            else:
                entity = EntityDAO.from_handle(
                    handle=token_obj.entity.handle,
                    owner_handle=token_obj.entity.owner_handle,
                )

            if not entity:
                raise HTTPException(
                    status_code=404,
                    detail="Entity from key not found",
                )

            infostar = cls.create_infostar_from_entity(
                entity, token_obj, request
            )
            creator = Creator.from_infostar(infostar)
            cls.CACHE[api_key_header] = (creator, infostar)

        request.state.infostar = infostar
        request.state.creator = creator

    @classmethod
    def can_impersonate(cls, token: TauthTokenDAO) -> bool:
        return True

    @staticmethod
    def find_one_token(id: str):
        collection = TauthTokenDAO.collection(
            alias=Settings.get().REDBABY_ALIAS
        )
        r = collection.find_one({"_id": PyObjectId(id), "deleted": False})
        if not r:
            raise HTTPException(
                status_code=404,
                detail="API Key not found",
            )

        return TauthTokenDAO(**r)

    @staticmethod
    def validate_token(token: TauthTokenDAO, secret: str):
        if hash_value(secret) == token.value_hash:
            return
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
        )

    @classmethod
    def create_infostar_from_entity(
        cls, entity: EntityDAO, token: TauthTokenDAO, request: Request
    ):
        owner_ref = entity.owner_ref.handle if entity.owner_ref else ""
        ip = get_request_ip(request)
        infostar = Infostar(
            request_id=PyObjectId(),
            apikey_name=token.name,
            authprovider_type="tauth-key",
            authprovider_org=owner_ref,
            extra={},
            service_handle="/tauth",
            user_handle=entity.handle,
            user_owner_handle=owner_ref,
            client_ip=ip,
        )
        return infostar
