from typing import Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from pymongo import errors as pymongo_errors
from redbaby.document import Document

from ..schemas import Infostar
from ..settings import Settings

T = TypeVar("T", bound=Document)


def create_one(item_in: BaseModel, model: Type[T], infostar: Infostar) -> T:
    item = model(**item_in.model_dump(), created_by=infostar)  # type: ignore
    try:
        res = model.collection(alias=Settings.get().REDBABY_ALIAS).insert_one(
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
