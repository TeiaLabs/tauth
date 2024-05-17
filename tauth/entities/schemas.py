from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from ..schemas.attribute import Attribute
from .models import EntityRef


class EntityIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(..., min_length=3, max_length=50)
    owner_handle: Optional[str] = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "org": {
                        "summary": "Minimal Organization",
                        "description": "A root-level organization with no authproviders registered.",
                        "value": {
                            "handle": "/orgname",
                            "owner_handle": None,
                            "type": "organization",
                        },
                    },
                    "org-user": {
                        "summary": "Minimal Organization User",
                        "description": 'A user registered in an organization. "owner_handle" must point to a valid organization handle.',
                        "value": {
                            "handle": "user@orgname.com",
                            "owner_handle": "/orgname",
                            "type": "user",
                        },
                    },
                }
            ]
        }
    )


class EntityIntermediate(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(...)
    owner_ref: Optional[EntityRef] = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]
