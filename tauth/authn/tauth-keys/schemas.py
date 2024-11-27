from pydantic import BaseModel, Field

from tauth.authz.roles.schemas import RoleRef
from tauth.entities.schemas import EntityRef, EntityRefIn


class TauthTokenCreationIn(BaseModel):
    name: str
    roles: list[RoleRef] = Field(default_factory=list)
    entity: EntityRefIn


class TauthTokenCreationIntermidiate(TauthTokenCreationIn):
    entity: EntityRef


class TauthTokenCreationOut(TauthTokenCreationIntermidiate):
    value: str
