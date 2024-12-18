from typing import Any

from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ...entities.schemas import EntityRef
from ...utils.teia_behaviors import Authoring


class ResourceDAO(Document, Authoring, ObjectIdMixin, ReadingMixin):
    service_ref: EntityRef
    resource_collection: str
    resource_identifier: str
    metadata: dict[str, Any]

    @classmethod
    def collection_name(cls) -> str:
        return "resources"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel(
                [
                    ("service_ref.handle", 1),
                    ("resource_collection", 1),
                ],
            ),
            IndexModel([("service_ref.handle", 1)]),
            IndexModel([("resource_identifier", 1)]),
            IndexModel(
                [
                    ("metadata.alias", 1),
                ],
                sparse=True,
            ),
            IndexModel(
                [
                    ("resource_collection", 1),
                    ("resource_identifier", 1),
                    ("metadata.alias", 1),
                ],
                sparse=True,
            ),
        ]
        return idxs
