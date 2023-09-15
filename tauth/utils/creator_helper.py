import secrets
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException
from fastapi import status as s
from pydantic import EmailStr, validate_email
from redb.interface.errors import DocumentNotFound, UniqueConstraintViolation

from ..models import TokenDAO, UserDAO
from ..schemas import Creator
from ..settings import Settings
from .access_helper import sanitize_client_name
from .token_helper import parse_token


@lru_cache(maxsize=32)
def validate_token_against_db(token: str, client_name: str, token_name: str):
    filters = {"client_name": client_name, "name": token_name}
    try:
        entity = TokenDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).find_one(filter=filters)
    except DocumentNotFound as e:
        d = {
            "filters": filters,
            "msg": f"Token does not exist for client.",
            "type": type(e).__name__,
        }
        raise HTTPException(status_code=s.HTTP_401_UNAUTHORIZED, detail=d)
    if not secrets.compare_digest(token, entity.value):
        code, m = s.HTTP_401_UNAUTHORIZED, "Token does not match."
        raise HTTPException(status_code=code, detail={"msg": m})
    return entity


def create_user_on_db(creator: Creator, token_creator_email: Optional[EmailStr]):
    user_creator_email = (
        creator.user_email if token_creator_email is None else token_creator_email
    )
    try:
        user = UserDAO(
            email=creator.user_email,
            client_name=creator.client_name,
            created_by=Creator(
                client_name=creator.user_email,
                token_name=creator.client_name,
                user_email=user_creator_email,
            ),
        )
        UserDAO.switch_db(Settings.get().TAUTH_MONGODB_DBNAME).insert_one(user)
    except UniqueConstraintViolation:
        pass


@lru_cache(maxsize=1024)
def get_request_creator(token: str, user_email: Optional[str]):
    client_name, token_name, _ = parse_token(token)
    client_name = sanitize_client_name(client_name)
    token_creator_user_email = None
    if client_name == "/":
        if user_email is None:
            code, m = s.HTTP_401_UNAUTHORIZED, "User email is required for root client."
            raise HTTPException(status_code=code, detail=m)
        if not secrets.compare_digest(token, Settings().TAUTH_ROOT_API_KEY):
            code, m = s.HTTP_401_UNAUTHORIZED, "Root token does not match env var."
            raise HTTPException(status_code=code, detail=m)
        try:
            validate_email(user_email)
        except:
            code, m = s.HTTP_401_UNAUTHORIZED, "User email is not valid."
            raise HTTPException(status_code=code, detail=m)
        request_creator_user_email = EmailStr(user_email)
    else:
        token_obj = validate_token_against_db(token, client_name, token_name)
        if user_email is None:
            request_creator_user_email = token_obj.created_by.user_email
        else:
            token_creator_user_email = token_obj.created_by.user_email
            try:
                validate_email(user_email)
            except:
                code, m = s.HTTP_401_UNAUTHORIZED, "User email is not valid."
                raise HTTPException(status_code=code, detail=m)
            request_creator_user_email = EmailStr(user_email)
    creator = Creator(
        client_name=client_name,
        token_name=token_name,
        user_email=request_creator_user_email,
    )
    create_user_on_db(creator, token_creator_user_email)
    return creator
