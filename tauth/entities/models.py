from typing import Literal, Optional

from pydantic import BaseModel
from pymongo import IndexModel
from redbaby.document import Document
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin

from ..schemas.attribute import Attribute
from ..schemas.infostar import Infostar
from ..utils.teia_behaviors import Authoring


class EntityRefBase(BaseModel):
    handle: str
    id: str

class EntityRef(EntityRefBase):
    type: Literal["organization", "service", "user"]


class OrganizationRef(EntityRefBase):
    type: Literal["organization"]


class ServiceRef(EntityRefBase):
    type: Literal["service"]


class UserRef(EntityRefBase):
    type: Literal["user"]


class EntityDAO(Document, Authoring, ReadingMixin, HashIdMixin):
    external_ids: list[Attribute]  # e.g., url, azuread-id/auth0-id, ...
    extra: list[Attribute]
    handle: str
    owner: Optional[EntityRef]
    roles: list[str]  # e.g.: ["teia-admin", "allai-user-basic"]
    type: Literal["user", "service", "organization"]
    updated_by: Infostar

    @classmethod
    def collection_name(cls) -> str:
        return "entities"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel("roles"),
            IndexModel([("type", 1), ("handle", 1), ("owner.handle", 1)], unique=True),
            IndexModel(
                [("type", 1), ("external_ids.name", 1), ("external_ids.value", 1)],
                unique=True,
            ),
        ]
        return idxs
