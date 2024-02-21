from pydantic import EmailStr
from pymongo import IndexModel
from redbaby.behaviors.hashids import HashIdDoc
from redbaby.document import Document

from ..schemas import Creator


class UserDAO(Document, HashIdDoc):
    client_name: str
    created_by: Creator
    email: EmailStr

    @classmethod
    def collection_name(cls) -> str:
        return "users"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [IndexModel([("client_name", 1), ("email", 1)], unique=True)]
        return idxs

    def hashable_fields(self) -> list[str]:
        return [self.client_name, self.email]


class TokenDAO(Document, HashIdDoc):
    client_name: str
    created_by: Creator
    name: str
    value: str

    @classmethod
    def collection_name(cls) -> str:
        return "tokens"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [IndexModel([("client_name", 1), ("name", 1)], unique=True)]
        return idxs

    def hashable_fields(self) -> list[str]:
        return [self.client_name, self.name]


class ClientDAO(Document, HashIdDoc):
    created_by: Creator
    name: str

    @classmethod
    def collection_name(cls) -> str:
        return "clients"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [IndexModel([("name", 1)], unique=True)]
        return idxs

    def hashable_fields(self) -> list[str]:
        return [self.name]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "/teialabs"},
                {"name": "/osf/allai"},
            ]
        }
    }
