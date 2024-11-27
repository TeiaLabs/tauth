from typing import Literal

from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ...entities.schemas import EntityRef
from ...utils.teia_behaviors import Authoring

PermissionType = Literal["resource", "generic"]


class PermissionDAO(Document, ObjectIdMixin, Authoring, ReadingMixin):
    name: str
    description: str
    entity_ref: EntityRef
    type: PermissionType

    @classmethod
    def collection_name(cls) -> str:
        return "authz-permissions"

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
            IndexModel([("type", 1)]),
        ]
        return idxs
