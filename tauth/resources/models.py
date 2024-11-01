from typing import Any

from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ..authz.roles.schemas import RoleRef
from ..entities.schemas import EntityRef
from ..utils.teia_behaviors import Authoring


class ResourceDAO(Document, Authoring, ObjectIdMixin, ReadingMixin):
    service_ref: EntityRef
    role_ref: RoleRef
    resource_collection: str
    ids: list[str]
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
                    ("role_ref.name", 1),
                    ("resource_collection", 1),
                ],
                unique=True,
            ),
            IndexModel([("service_ref.handle", 1)]),
            IndexModel([("role_ref.name", 1)]),
        ]
        return idxs
