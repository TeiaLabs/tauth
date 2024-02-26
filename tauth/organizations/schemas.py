from datetime import datetime

from pydantic import BaseModel, Field

from ..schemas import Creator
from .models import Attribute


class OrganizationIn(BaseModel):
    name: str
    external_ids: list[Attribute]


class GeneratedFields(BaseModel):
    id: str = Field(alias="_id")
    created_by: Creator
    created_at: datetime
