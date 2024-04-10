from pydantic import BaseModel, Field
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.document import Document

from ..schemas import Creator
from ..schemas.attribute import Attribute


class OrganizationDAO(Document, HashIdMixin):
    name: str
    created_by: Creator
    external_ids: list[Attribute] = Field(default_factory=list)

    def hashable_fields(self) -> list[str]:
        return [self.name]

    @classmethod
    def collection_name(cls) -> str:
        return "organizations"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("name", unique=True),
            IndexModel([("external_ids.name", 1), ("external_ids.value", 1)], unique=True),
        ]
        return idxs
