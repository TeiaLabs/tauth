from pydantic import BaseModel

from .models import Attribute


class OrganizationIn(BaseModel):
    name: str
    external_ids: list[Attribute]
