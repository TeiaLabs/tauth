from typing import Type, TypeVar, cast

from cacheia_client import Client as CacheiaClient
from cacheia_client.client import CachedValue
from fastapi import HTTPException
from redbaby.behaviors import ReadingMixin
from redbaby.pyobjectid import PyObjectId

from ..schemas import Infostar
from ..settings import Settings

T = TypeVar("T", bound=ReadingMixin)


def read_many(infostar: Infostar, model: Type[T], **filters) -> list[T]:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = model.find(
        filter=query,
        alias=Settings.get().TAUTH_REDBABY_ALIAS,
        validate=True,
        lazy=False,
    )
    return objs


def read_one(infostar: Infostar, model: Type[T], identifier: PyObjectId | str) -> T:
    filters = {"_id": identifier}
    item = model.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find_one(filters)
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Document with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    return item


def get_cacheia_key(infostar: Infostar, model: Type[T], **filters) -> str:
    key = f"{model.__name__}"
    # key += f"__{infostar.model_dump(exclude={"request_id"})}"
    key += f"__{filters}"
    return key


def read_one_filters(infostar: Infostar, model: Type[T], **filters) -> T:
    # caching
    cache = CacheiaClient()
    cache_key = get_cacheia_key(infostar, model, **filters)
    try:
        if value := cache.get_key(cache_key):
            value = value.value
            value = cast(T, value)
            return value
    except KeyError:
        pass

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

    # add to cache
    cached_value = CachedValue(key=cache_key, value=items[0])
    cache.cache(cached_value)
    return items[0]
