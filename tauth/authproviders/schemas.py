from typing import Literal, Optional

from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from .models import OrganizationRef, ServiceRef
from ..schemas.attribute import Attribute


class AuthProviderIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    organization_name: str
    service_name: Optional[str] = Field(None)
    type: Literal["auth0", "melt-key", "tauth-key"]


class AuthProviderRef(BaseModel):
    id: PyObjectId = Field(alias="_id")
    organizaion_ref: OrganizationRef
    service_ref: Optional[ServiceRef]
    type: Literal["auth0", "melt-key", "tauth-key"]
