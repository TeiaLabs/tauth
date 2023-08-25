from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class Creator(BaseModel):
    client_name: str
    token_name: str
    user_email: EmailStr
    user_ip: str = "127.0.0.1"


class UserCreation(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    created_at: datetime
    created_by: Creator
    email: EmailStr


class TokenCreationOut(BaseModel):
    created_by: Creator
    created_at: datetime
    name: str
    value: str


class TokenMeta(BaseModel):
    created_at: datetime
    created_by: Creator
    name: str


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


class TokenCreation(BaseModel):
    name: str
