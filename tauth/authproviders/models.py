from typing import Literal, Optional

from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ..schemas import Creator
from ..schemas.attribute import Attribute
from ..entities.models import ServiceRef, OrganizationRef
from ..utils.teia_behaviors import Authoring


class AuthProviderDAO(Document, Authoring, HashIdMixin, ReadingMixin):
    created_by: Creator
    external_ids: list[Attribute] = Field(default_factory=list)  # dynamic provider selection
    extra: list[Attribute]
    name: str
    owner: OrganizationRef
    service_ref: Optional[ServiceRef]
    type: Literal["auth0", "melt-key", "tauth-key"]

    def hashable_fields(self) -> list[str]:
        return [self.name, self.owner.handle]

    @classmethod
    def collection_name(cls) -> str:
        return "authproviders"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel([("name", 1), ("owner", 1)], unique=True),
        ]
        return idxs
