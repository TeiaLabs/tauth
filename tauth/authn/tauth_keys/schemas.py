from datetime import datetime

from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from tauth.authz.roles.schemas import RoleRef
from tauth.entities.schemas import EntityRef, EntityRefIn
from tauth.schemas.infostar import Infostar


class TauthTokenCreationIn(BaseModel):
    name: str
    roles: list[RoleRef] = Field(default_factory=list)
    entity: EntityRefIn


class TauthTokenCreationIntermidiate(TauthTokenCreationIn):
    entity: EntityRef


class TauthTokenCreationOut(TauthTokenCreationIntermidiate):
    value: str


class TauthTokenDTO(BaseModel):
    id: PyObjectId
    name: str
    roles: list[RoleRef] = Field(default_factory=list)
    entity: EntityRef
    created_by: Infostar
    created_at: datetime
    updated_at: datetime
