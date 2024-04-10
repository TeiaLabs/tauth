from typing import Literal, Optional

from pydantic import BaseModel, Field

from .models import OrganizationRef, ServiceRef
from ..schemas.attribute import Attribute


class AuthProviderIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)  # dynamic provider selection
    extra: list[Attribute] = Field(default_factory=list)
    name: str
    owner: OrganizationRef
    service_ref: Optional[ServiceRef] = Field(None)
    type: Literal["auth0", "melt-key", "tauth-key"]
