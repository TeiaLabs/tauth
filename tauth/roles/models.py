from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ..entities.models import EntityRef
from ..utils.teia_behaviors import Authoring


class RoleDAO(Document, ObjectIdMixin, Authoring, ReadingMixin):
    name: str
    description: str
    entity_ref: EntityRef
    permissions: list[str] = Field(default_factory=list)

    @classmethod
    def collection_name(cls) -> str:
        return "roles"

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
