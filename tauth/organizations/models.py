from pydantic import BaseModel, Field
from redb.core import ClassField, CompoundIndex, Document, Index
from redb.core.mixins import SwitcharooMixin

from ..schemas import Creator


class Attribute(BaseModel):
    name: str
    value: str


class OrganizationDAO(Document, SwitcharooMixin):
    name: str  # /loreal or /nike
    created_by: Creator
    external_ids: list[Attribute] = Field(default_factory=list)

    @classmethod
    def collection_name(cls) -> str:
        return "organizations"

    @classmethod
    def get_indexes(cls) -> list[Index | CompoundIndex]:
        idxs = [
            Index(cls.name, unique=True),  # type: ignore
            CompoundIndex([cls.external_ids[0].name, cls.external_ids[0].value], unique=True),  # type: ignore
        ]
        return idxs

    @classmethod
    def get_hashable_fields(cls) -> list[ClassField]:
        return [cls.name]  # type: ignore
