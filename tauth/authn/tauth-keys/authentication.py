from fastapi import HTTPException, Request

from ...entities.models import EntityDAO
from ...schemas import Creator, Infostar
from ...settings import Settings
from ..utils import SizedCache
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
    ):
        db_id, secret = parse_key(api_key_header)

        token_obj = cls.find_one_token(db_id)

        cls.validate_token(token_obj, secret)

        entity = EntityDAO.from_handle(
            handle=token_obj.entity.handle,
            owner_handle=token_obj.entity.owner_handle,
        )
        if not entity:
            raise HTTPException(
                status_code=404,
                detail="Entity from key not found",
            )

    @staticmethod
    def find_one_token(id: str):
        collection = TauthTokenDAO.collection(
            alias=Settings.get().REDBABY_ALIAS
        )
        r = collection.find_one({"_id": id})
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
            status_code=403,
            detail="Invalid API Key",
        )

    def create_infostar_from_entity(entity: EntityDAO, token: TauthTokenDAO):
        infostar = Infostar(
                request_id=PyObjectId,
                apikey_name=token.name,
                authprovider_type="tauth-key",
                authprovider_org=entity.owner_handle,
                extra=,
                service_handle=,
                user_handle= ,
                user_owner_handle= ,
                client_ip= ,
        )

