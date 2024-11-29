from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.behaviors.timestamping import Timestamping
from redbaby.document import Document
from redbaby.pyobjectid import PyObjectId

from ...entities.schemas import EntityRef
from ...utils.teia_behaviors import Authoring
from .schemas import TauthTokenDTO


class TauthTokenDAO(
    Document, Authoring, ObjectIdMixin, ReadingMixin, Timestamping
):
    name: str
    value_hash: str
    roles: list[PyObjectId] = Field(default_factory=list)
    deleted: bool = Field(default=False)
    entity: EntityRef

    @classmethod
    def collection_name(cls) -> str:
        return "tauth-keys"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel([("name", 1)]),
            IndexModel(
                [
                    ("name", 1),
                    ("entity.handle", 1),
                    ("entity.owner_handle", 1),
                ],
                unique=True,
            ),
        ]
        return idxs

    def to_dto(self):
        return TauthTokenDTO(
            id=self.id,
            name=self.name,
            roles=self.roles,
            entity=self.entity,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
