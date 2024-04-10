from typing import Literal, Optional

from pydantic import BaseModel, Field

from .models import EntityRef
from ..schemas.attribute import Attribute


class EntityIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    handle: str = Field(..., min_length=3, max_length=50)
    owner: Optional[EntityRef] = Field(None)
    roles: list[str] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]
