from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document
from redbaby.pyobjectid import PyObjectId

from ...entities.schemas import EntityRef
from ...utils.teia_behaviors import Authoring
from .schemas import RoleRef


class RoleDAO(Document, ObjectIdMixin, Authoring, ReadingMixin):
    name: str
    description: str
    entity_ref: EntityRef
    permissions: list[PyObjectId] = Field(default_factory=list)

    @classmethod
    def collection_name(cls) -> str:
        return "authz-roles"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel(
                [("entity_ref.handle", 1), ("name", 1)],
                unique=True,
            ),
            IndexModel(
                [("entity_ref.handle", 1)],
            ),
        ]
        return idxs

    @classmethod
    def from_ref(cls, ref: RoleRef) -> "RoleDAO | None":
        collection = cls.collection(alias="tauth")
        role = collection.find_one({"_id": ref.id})
        if role:
            return RoleDAO(**role)

    @classmethod
    def from_name(cls, name: str, entity_handle: str) -> "RoleDAO | None":
        collection = cls.collection(alias="tauth")
        role = collection.find_one(
            {"entity_ref.handle": entity_handle, "name": name}
        )
        if role:
            return RoleDAO(**role)
