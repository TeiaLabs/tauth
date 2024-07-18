from typing import Literal

from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ...utils.teia_behaviors import Authoring


class AuthorizationPolicyDAO(Document, Authoring, ObjectIdMixin, ReadingMixin):
    description: str
    name: str
    policy: str
    type: Literal["opa"]

    @classmethod
    def collection_name(cls) -> str:
        return "authorization-policies"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel([("name", 1), ("type", 1)], unique=True),
            IndexModel([("type", 1)]),
        ]
        return idxs

    def hashable_fields(self) -> list[str]:
        return [self.name, self.type]
