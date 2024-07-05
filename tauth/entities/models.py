from typing import Literal, Optional

from pydantic import BaseModel, Field
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ..schemas.attribute import Attribute
from ..utils.teia_behaviors import Authoring


class EntityRefBase(BaseModel):
    handle: str


class EntityRef(EntityRefBase):
    type: Literal["organization", "service", "user"]


class OrganizationRef(EntityRefBase):
    type: Literal["organization"] = "organization"


class ServiceRef(EntityRefBase):
    type: Literal["service"] = "service"


class UserRef(EntityRefBase):
    type: Literal["user"] = "user"


class EntityDAO(Document, Authoring, ReadingMixin, HashIdMixin):
    external_ids: list[Attribute] = Field(
        default_factory=list
    )  # e.g., url, azuread-id/auth0-id, ...
    extra: list[Attribute] = Field(default_factory=list)
    handle: str
    owner_ref: Optional[EntityRef]
    roles: list[str] = Field(
        default_factory=list
    )  # e.g.: ["teia-admin", "allai-user-basic"]
    type: Literal["user", "service", "organization"]

    @classmethod
    def collection_name(cls) -> str:
        return "entities"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("roles"),
            IndexModel(
                [("type", 1), ("handle", 1), ("owner_ref.handle", 1)], unique=True
            ),
            IndexModel(
                [("type", 1), ("external_ids.name", 1), ("external_ids.value", 1)],
            ),
        ]
        return idxs

    @classmethod
    def from_handle(cls, handle: str) -> Optional["EntityDAO"]:
        out = cls.collection(alias="tauth").find_one({"handle": handle})
        if out:
            return EntityDAO(**out)

    @classmethod
    def from_handle_to_ref(cls, handle: str) -> Optional[EntityRef]:
        entity = cls.from_handle(handle)
        if entity:
            return EntityRef(type=entity.type, handle=entity.handle, id=entity.id)

    def to_ref(self) -> EntityRef:
        return EntityRef(type=self.type, handle=self.handle, id=self.id)

    def hashable_fields(self) -> list[str]:
        l = [self.handle]
        if self.owner_ref:
            l.append(self.owner_ref.handle)
        return l
