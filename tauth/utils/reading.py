from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from redbaby.behaviors import ReadingMixin
from redbaby.pyobjectid import PyObjectId

from ..schemas import Infostar
from ..settings import Settings

T = TypeVar("T", bound=ReadingMixin)
Z = TypeVar("Z", bound=BaseModel)
U = TypeVar("U")
X = TypeVar("X")


def read_many(infostar: Infostar, model: type[T], **filters) -> list[T]:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = model.find(
        filter=query,
        alias=Settings.get().REDBABY_ALIAS,
        validate=True,
        lazy=False,
    )
    return objs


def read_one(
    infostar: Infostar, model: type[T], identifier: PyObjectId | str
) -> T:
    if isinstance(identifier, str):
        identifier = PyObjectId(identifier)
    filters = {"_id": identifier}
    item = model.collection(alias=Settings.get().REDBABY_ALIAS).find_one(
        filters
    )
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Document with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    item = model.model_validate(item)
    return item


def read_one_filters(infostar: Infostar, model: type[T], **filters) -> T:
    print(filters)
    f = {k: v for k, v in filters.items() if v is not None}
    items = model.find(
        f,
        alias=Settings.get().REDBABY_ALIAS,
        validate=True,
        lazy=False,
    )
    print(items)
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


def aggregate(
    model: type[T],
    pipeline: list[dict[str, Any]],
    formatter: (
        Callable[[dict[str, Any]], Z]
        | Callable[[dict[str, Any]], T]
        | Callable[[dict[str, Any]], X]
        | None
    ) = None,
) -> Iterable[Z] | Iterable[T] | Iterable[X]:

    collection = model.collection(alias=Settings.get().REDBABY_ALIAS)

    result = collection.aggregate(pipeline)

    if formatter is None:
        formatter = lambda x: model(**x)

    return map(formatter, result)  # type: ignore
