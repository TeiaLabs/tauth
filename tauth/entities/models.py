from collections.abc import Iterator
from typing import Literal

from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

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
    role_refs: list[RoleRef] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]

    @classmethod
    def collection_name(cls) -> str:
        return "entities"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("role_refs.id"),
            IndexModel("handle"),
            IndexModel(
                [("type", 1), ("handle", 1), ("owner_ref.handle", 1)], unique=True
            ),
            IndexModel(
                [("external_ids.name", 1), ("external_ids.value", 1)],
            ),
        ]
        return idxs

    @classmethod
    def from_handle(cls, handle: str) -> "EntityDAO | None":
        out = cls.collection(alias="tauth").find_one({"handle": handle})
        if out:
            return EntityDAO(**out)

    @classmethod
    def from_handle_to_ref(cls, handle: str) -> EntityRef | None:
        entity = cls.from_handle(handle)
        if entity:
            return EntityRef(type=entity.type, handle=entity.handle)

    def to_ref(self) -> EntityRef:
        return EntityRef(type=self.type, handle=self.handle)

    def hashable_fields(self) -> list[str]:
        fields = [self.handle]
        return fields


class EntityRelationshipsDAO(Document, Authoring, ReadingMixin, HashIdMixin):
    origin: EntityRef
    target: EntityRef
    type: Literal["parent", "child"]

    @classmethod
    def collection_name(cls) -> str:
        return "entities_relationships"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("type"),
            IndexModel("origin.handle"),
            IndexModel("target.handle"),
            IndexModel([("origin.handle", 1), ("target.handle", 1)], unique=True),
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
