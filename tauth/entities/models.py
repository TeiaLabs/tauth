from collections.abc import Iterator
from typing import Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document
from redbaby.pyobjectid import PyObjectId

from ..authz.roles.schemas import RoleRef
from ..schemas.attribute import Attribute
from ..utils.teia_behaviors import Authoring
from .schemas import EntityRef


class EntityDAO(Document, Authoring, ReadingMixin, HashIdMixin):
    external_ids: list[Attribute] = Field(
        default_factory=list
    )  # e.g., url, azuread-id/auth0-id, ...
    extra: list[Attribute] = Field(default_factory=list)
    handle: str
    owner_ref: EntityRef | None = None
    roles: list[RoleRef] = Field(default_factory=list)
    permissions: list[PyObjectId] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]

    @classmethod
    def collection_name(cls) -> str:
        return "entities"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("roles.id"),
            IndexModel(
                [("type", 1), ("handle", 1), ("owner_ref.handle", 1)],
                unique=True,
            ),
            IndexModel(
                [
                    ("type", 1),
                    ("external_ids.name", 1),
                    ("external_ids.value", 1),
                ],
            ),
        ]
        return idxs

    @classmethod
    def from_handle(
        cls, handle: str, owner_handle: str | None
    ) -> Optional["EntityDAO"]:
        filters = {"handle": handle}
        if owner_handle:
            filters["owner_ref.handle"] = owner_handle
        out = cls.collection(alias="tauth").find_one(filters)
        if out:
            return EntityDAO(**out)

    @classmethod
    def from_handle_assert(
        cls,
        handle: str,
        owner_handle: str | None,
    ) -> "EntityDAO":
        entity = cls.from_handle(handle, owner_handle)
        if entity is None:

            raise HTTPException(
                status_code=404,
                detail=f"Entity with handle {handle} not found",
            )
        return entity

    @classmethod
    def from_handle_to_ref(
        cls, handle: str, owner_handle: str | None
    ) -> EntityRef | None:
        entity = cls.from_handle(handle, owner_handle)
        if entity:
            return EntityRef(
                type=entity.type,
                handle=entity.handle,
                owner_handle=(
                    entity.owner_ref.handle if entity.owner_ref else None
                ),
            )

    def to_ref(self) -> EntityRef:
        return EntityRef(
            type=self.type,
            handle=self.handle,
            owner_handle=self.owner_ref.handle if self.owner_ref else None,
        )

    def hashable_fields(self) -> list[str]:
        fields = [self.handle]
        if self.owner_ref:
            fields.append(self.owner_ref.handle)
        return fields


class EntityRelationshipsDAO(Document, Authoring, ReadingMixin, HashIdMixin):
    origin: EntityRef
    target: EntityRef
    type: Literal["parent", "child"]

    @classmethod
    def collection_name(cls) -> str:
        return "entities-relationships"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("type"),
            IndexModel("origin.handle"),
            IndexModel("target.handle"),
            IndexModel(
                [("origin.handle", 1), ("target.handle", 1)], unique=True
            ),
        ]
        return idxs

    @classmethod
    def from_origin(cls, handle: str) -> Iterator[EntityDAO]:
        cursor = cls.collection(alias="tauth").find({"origin.handle": handle})
        return map(lambda x: EntityDAO(**x), cursor)

    @classmethod
    def from_target(cls, handle: str) -> Iterator[EntityDAO]:
        cursor = cls.collection(alias="tauth").find({"target.handle": handle})
        return map(lambda x: EntityDAO(**x), cursor)

    def hashable_fields(self) -> list[str]:
        fields = [self.type, self.origin.handle, self.target.handle]
        return fields


class EntityIntermediate(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(...)
    owner_ref: EntityRef | None = Field(None)
    roles: list[RoleRef] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]
