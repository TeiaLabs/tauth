from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.behaviors.timestamping import Timestamping
from redbaby.document import Document

from tauth.authz.roles.schemas import RoleRef

from ...entities.schemas import EntityRef
from ...utils.teia_behaviors import Authoring


class TauthTokenDAO(
    Document, Authoring, HashIdMixin, ReadingMixin, Timestamping
):
    name: str
    value_hash: str
    roles: list[RoleRef] = Field(default_factory=list)
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

    def hashable_fields(self):
        fs = [self.name, self.entity.handle]
        if self.entity.owner_handle:
            fs.append(self.entity.owner_handle)

        return fs
