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
                    "Org": {
                        "summary": "Minimal Organization Example",
                        "description": "A **normal** item works correctly.",
                        "value": {
                            "handle": "/teialabs",
                            "owner_handle": None,
                            "type": "organization",
                        },
                    }
                }
            ]
        }
    )


class EntityIntermediate(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(..., min_length=3, max_length=50)
    owner_ref: Optional[EntityRef] = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]
