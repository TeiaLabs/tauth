from fastapi import HTTPException, Request
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from tauth.authz.policies.schemas import AuthorizationDataIn

from ...authz.controllers import authorize
from ...authz.utils import get_permission_set_from_roles
from ...entities.models import EntityDAO
from ...schemas import Creator, Infostar
from ..utils import SizedCache, get_request_ip
from .keygen import hash_value
from .models import TauthTokenDAO
from .utils import TauthKeyParseError, parse_key

EmailStr = str


class RequestAuthenticator:
    CACHE: SizedCache[str, tuple[Creator, Infostar]] = SizedCache(max_size=512)

    @classmethod
    async def validate(
        cls,
        request: Request,
        api_key_header: str,
        impersonate_handle: str | None,
        impersonate_owner_handle: str | None,
    ):
        if api_key_header in cls.CACHE and impersonate_handle is None:
            creator, infostar = cls.CACHE[api_key_header]

        else:
            try:
                db_id, secret = parse_key(api_key_header)
            except TauthKeyParseError:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Tauth Key format",
                )

            token_obj = TauthTokenDAO.find_one_token(db_id)

            cls.validate_token(token_obj, secret)

            entity = EntityDAO.from_handle_assert(
                handle=token_obj.entity.handle,
                owner_handle=token_obj.entity.owner_handle,
            )
            original_entity = None
            if impersonate_handle is not None:
                await cls.can_impersonate(request, entity, token_obj)
                logger.info(
                    f"Impersonating {impersonate_handle} on behalf of {token_obj.entity.handle}"
                )
                original_entity = entity
                entity = EntityDAO.from_handle_assert(
                    handle=impersonate_handle,
                    owner_handle=impersonate_owner_handle,
                )

            infostar = cls.create_infostar_from_entity(
                entity,
                token_obj,
                request,
                request_id=PyObjectId(),
                original=original_entity,
            )
            creator = Creator.from_infostar(infostar)
            cls.CACHE[api_key_header] = (creator, infostar)

        request.state.infostar = infostar
        request.state.creator = creator

    @classmethod
    async def can_impersonate(
        cls, request: Request, entity: EntityDAO, token: TauthTokenDAO
    ):
        token_permissions = get_permission_set_from_roles(token.roles)
        res = await authorize(
            request,
            entity,
            authz_data=AuthorizationDataIn(
                context=dict(), policy_name="impersonate", rule="allow"
            ),
            allowed_permissions=token_permissions,
        )
        if res.authorized is False:
            raise HTTPException(
                status_code=401,
                detail="You are not authorized to impersonate this entity",
            )

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
        cls,
        entity: EntityDAO,
        token: TauthTokenDAO,
        request: Request,
        request_id: PyObjectId,
        original: EntityDAO | None = None,
    ) -> Infostar:
        owner_ref = entity.owner_ref.handle if entity.owner_ref else ""
        ip = get_request_ip(request)
        infostar = Infostar(
            request_id=request_id,
            apikey_name=token.name,
            authprovider_type="tauth-key",
            authprovider_org=owner_ref,
            extra={},
            service_handle="/tauth",
            user_handle=entity.handle,
            user_owner_handle=owner_ref,
            client_ip=ip,
            original=(
                cls.create_infostar_from_entity(
                    entity=original,
                    token=token,
                    request=request,
                    request_id=request_id,
                    original=None,
                )
                if original
                else None
            ),
        )
        return infostar
