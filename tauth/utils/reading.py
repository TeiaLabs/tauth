from typing import Type, TypeVar

from cacheia_decorators.remote import cache
from crypteia import Multibasing, Multihashing, ToBytes, compose
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
    if isinstance(identifier, str):
        identifier = PyObjectId(identifier)
    filters = {"_id": identifier}
    item = model.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find_one(filters)
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Document with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    item = model.model_validate(item)
    return item


def get_cacheia_key(infostar: Infostar, model: Type[T], **filters) -> str:
    key = f"{model.__name__}"
    # key += f"__{infostar.model_dump(exclude={"request_id"})}"
    key += f"__{filters}"
    get_hash = compose(ToBytes(), Multihashing("sha3-224"), Multibasing("base58btc"))
    digest = get_hash(key)
    return digest


# @cache(key_builder=get_cacheia_key)
def read_one_filters(infostar: Infostar, model: Type[T], **filters) -> T:
    f = {k: v for k, v in filters.items() if v is not None}
    items = model.find(
        f,
        alias=Settings.get().TAUTH_REDBABY_ALIAS,
        validate=True,
        lazy=False,
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
