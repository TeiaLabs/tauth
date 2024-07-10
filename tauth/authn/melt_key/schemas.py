from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from ...schemas import Creator, Infostar


class TokenMeta(BaseModel):
    created_at: datetime
    created_by: Infostar
    name: str


class TokenCreationIntermediate(BaseModel):
    client_name: str
    name: str
    value: str


class TokenCreationOut(TokenMeta):
    value: str


class UserCreation(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    created_at: datetime
    created_by: Creator
    email: EmailStr


class ClientCreation(BaseModel):
    name: str


class ClientCreationOut(BaseModel):
    created_at: datetime
    created_by: Creator
    id: str = Field(alias="_id")
    name: str
    tokens: list[TokenCreationOut]
    users: list[UserOut]


class ClientOut(BaseModel):
    created_at: datetime
    created_by: Creator
    id: str = Field(alias="_id")
    name: str


class ClientOutJoinTokensAndUsers(BaseModel):
    created_at: datetime
    created_by: Creator
    id: str = Field(alias="_id")
    name: str
    tokens: list[TokenMeta]
    users: list[UserOut]
