from pydantic import EmailStr, computed_field
from pymongo import IndexModel
from redbaby.document import Document

from ..schemas import Creator


class UserDAO(Document):
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

    @computed_field
    def _id(self):
        return str([self.client_name, self.email])


class TokenDAO(Document):
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

    @computed_field
    def _id(self):
        return str([self.client_name, self.name])


class ClientDAO(Document):
    created_by: Creator
    name: str

    @classmethod
    def collection_name(cls) -> str:
        return "clients"

    @classmethod
    def get_indexes(cls) -> list[IndexModel]:
        idxs = [IndexModel([(cls.name, 1)], unique=True)]
        return idxs

    @computed_field
    def _id(self):
        return str([self.name])

    class Config:
        schema_extra = {
            "examples": [
                {"name": "/teialabs"},
                {"name": "/teialabs/datasources"},
            ]
        }
