from typing import Type, TypeVar

from fastapi import HTTPException
from redbaby.pyobjectid import PyObjectId
from redbaby.behaviors import ReadingMixin

from ..schemas import Creator
from ..settings import Settings

T = TypeVar("T", bound=ReadingMixin)


def read_many(creator: Creator, model: Type[T], **filters) -> list:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = model.find(filter=query, alias=Settings.get().TAUTH_REDBABY_ALIAS)
    return objs


def read_one(model: Type[T], identifier: PyObjectId | str) -> T:
    filters = {"_id": identifier}
    item = model.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find_one(filters)
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Organization with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    return item

