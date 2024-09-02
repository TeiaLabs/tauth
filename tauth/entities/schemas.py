from typing import Literal, Optional

from fastapi.openapi.models import Example
from pydantic import BaseModel, Field

from ..schemas.attribute import Attribute


class EntityRefBase(BaseModel):
    handle: str


class EntityRef(EntityRefBase):
    type: Literal["organization", "service", "user"]


class OrganizationRef(EntityRefBase):
    type: Literal["organization"] = "organization"


class ServiceRef(EntityRefBase):
    type: Literal["service"] = "service"


class UserRef(EntityRefBase):
    type: Literal["user"] = "user"


class EntityIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(..., min_length=3, max_length=50)
    owner_handle: Optional[str] = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]

    @staticmethod
    def get_entity_examples():
        examples = {
            "Minimal Organization": Example(
                description="A root-level organization with no authproviders registered.",
                value=EntityIn(
                    handle="/orgname",
                    owner_handle=None,
                    type="organization",
                ),
            ),
            "Minimal Organization User": Example(
                description=(
                    "A user registered in an organization. "
                    "'owner_handle' must point to a valid organization handle."
                ),
                value=EntityIn(
                    handle="user@orgname.com",
                    owner_handle="/orgname",
                    type="user",
                ),
            ),
        }
        return examples


class EntityIntermediate(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(...)
    owner_ref: Optional[EntityRef] = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]
