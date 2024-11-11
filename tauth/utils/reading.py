from typing import Any, Dict, List, Type, TypeVar

from crypteia import Multibasing, Multihashing, ToBytes, compose
from fastapi import HTTPException
from pydantic import BaseModel
from redbaby.behaviors import ReadingMixin
from redbaby.pyobjectid import PyObjectId

from ..schemas import Infostar
from ..settings import Settings

T = TypeVar("T", bound=ReadingMixin)
Z = TypeVar("Z", bound=BaseModel)


def read_many(infostar: Infostar, model: Type[T], **filters) -> list[T]:
    query = {k: v for k, v in filters.items() if v is not None}
    objs = model.find(
        filter=query,
        alias=Settings.get().REDBABY_ALIAS,
        validate=True,
        lazy=False,
    )
    return objs


def read_one(infostar: Infostar, model: Type[T], identifier: PyObjectId | str) -> T:
    if isinstance(identifier, str):
        identifier = PyObjectId(identifier)
    filters = {"_id": identifier}
    item = model.collection(alias=Settings.get().REDBABY_ALIAS).find_one(filters)
    if not item:
        d = {
            "error": "DocumentNotFound",
            "msg": f"Document with filters={filters} not found.",
        }
        raise HTTPException(status_code=404, detail=d)
    item = model.model_validate(item)
    return item


def read_one_filters(infostar: Infostar, model: Type[T], **filters) -> T:
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
    model: Type[T],
    pipeline: List[dict[str, Any]],
    result_model: Type[Z],
) -> List[Z]:
    try:
        results = model.collection(alias=Settings.get().REDBABY_ALIAS).aggregate(
            pipeline
        )

        validated_results = [result_model.model_validate(result) for result in results]

        return validated_results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "AggregationError", "msg": str(e)}
        )
