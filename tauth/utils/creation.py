from typing import Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from pymongo import errors as pymongo_errors

from ..schemas import Creator
from ..settings import Settings
from .teia_behaviors import Authoring

T = TypeVar("T", bound=Authoring)


def create_one(item_in: BaseModel, model: Type[T], creator: Creator) -> T:
    item = model(**item_in.model_dump(), created_by=creator)
    try:
        res = model.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).insert_one(
            item.bson()
        )
    except pymongo_errors.DuplicateKeyError as e:
        d = {
            "error": e.__class__.__name__,
            "msg": e._message,
            "details": e.details,
        }
        raise HTTPException(status_code=409, detail=d)
    # TODO: add logging
    # TODO: add event tracking
    return item