from typing import Literal

from fastapi.openapi.models import Example
from pydantic import BaseModel, Field

from ..schemas.attribute import Attribute


class EntityRefBase(BaseModel):
    handle: str
    owner_handle: str | None = None


class EntityRefIn(EntityRefBase):
    pass


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
    owner_ref: EntityRefIn | None = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]

    @staticmethod
    def get_entity_examples():
        examples = {
            "Minimal Organization": Example(
                description="A root-level organization with no authproviders registered.",
                value=EntityIn(
                    handle="/orgname",
                    owner_ref=None,
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
                    owner_ref=EntityRefIn(handle="/orgname"),
                    type="user",
                ),
            ),
        }
        return examples
