from typing import Type, TypeVar

from fastapi import HTTPException
from redbaby.behaviors import ReadingMixin
from redbaby.pyobjectid import PyObjectId

from ..schemas import Creator
from ..settings import Settings

T = TypeVar("T", bound=ReadingMixin)


def read_many(creator, model: Type[T], **filters) -> list:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = model.find(
        filter=query,
        alias=Settings.get().TAUTH_REDBABY_ALIAS,
        validate=True,
        lazy=False,
    )
    return objs


def read_one(creator, model: Type[T], identifier: PyObjectId | str) -> T:
    filters = {"_id": identifier}
    item = model.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find_one(filters)
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Document with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    return item


def read_one_filters(creator, model: Type[T], **filters) -> T:
    f = {k: v for k, v in filters.items() if v is not None}
    items = model.find(
        f, alias=Settings.get().TAUTH_REDBABY_ALIAS, validate=True, lazy=False
    )
    if not items:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Document with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    if len(items) > 1:
        d = {
            "error": "DocumentNotUnique",
            "msg": f"Document with filters={filters} not unique.",
        }
        raise HTTPException(status_code=409, detail=d)
    return items[0]
