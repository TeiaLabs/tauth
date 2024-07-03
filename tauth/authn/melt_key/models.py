from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ...utils.teia_behaviors import Authoring


class TokenDAO(Document, Authoring, ReadingMixin, HashIdMixin):
    client_name: str
    name: str
    value: str

    @classmethod
    def collection_name(cls) -> str:
        return "melt-keys"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [IndexModel([("client_name", 1), ("name", 1)], unique=True)]
        return idxs

    def hashable_fields(self) -> list[str]:
        return [self.client_name, self.name]
