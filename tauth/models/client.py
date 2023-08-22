from pydantic import EmailStr
from redb.core import ClassField, CompoundIndex, Document, Index
from redb.core.mixins import SwitcharooMixin

from ..schemas import Creator


class UserDAO(Document, SwitcharooMixin):
    client_name: str
    created_by: Creator
    email: EmailStr

    @classmethod
    def collection_name(cls) -> str:
        return "users"

    @classmethod
    def get_indexes(cls) -> list[CompoundIndex]:
        idxs = [CompoundIndex([cls.client_name, cls.email], unique=True)]  # type: ignore
        return idxs

    @classmethod
    def get_hashable_fields(cls) -> list[ClassField]:
        return [cls.client_name, cls.email]  # type: ignore


class TokenDAO(Document, SwitcharooMixin):
    client_name: str
    created_by: Creator
    name: str
    value: str

    @classmethod
    def collection_name(cls) -> str:
        return "tokens"

    @classmethod
    def get_indexes(cls) -> list[CompoundIndex]:
        idxs = [CompoundIndex([cls.client_name, cls.name], unique=True)]  # type: ignore
        return idxs

    @classmethod
    def get_hashable_fields(cls) -> list[ClassField]:
        return [cls.client_name, cls.name]  # type: ignore


class ClientDAO(Document, SwitcharooMixin):
    created_by: Creator
    name: str

    @classmethod
    def collection_name(cls) -> str:
        return "clients"

    @classmethod
    def get_indexes(cls) -> list[Index]:
        idxs = [Index(cls.name, unique=True)]  # type: ignore
        return idxs

    @classmethod
    def get_hashable_fields(cls) -> list[ClassField]:
        return [cls.name]  # type: ignore

    class Config:
        schema_extra = {
            "examples": [
                {"name": "/teialabs"},
                {"name": "/teialabs/datasources"},
            ]
        }
