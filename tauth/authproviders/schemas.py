from typing import Any, Literal, Optional, Self

from pydantic import BaseModel, Field, ValidationInfo, model_validator
from pydantic.config import ConfigDict
from redbaby.pyobjectid import PyObjectId

from ..schemas.attribute import Attribute
from .models import OrganizationRef, ServiceRef


class AuthProviderIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    organization_name: str
    service_name: Optional[str] = Field(None)
    type: Literal["auth0", "melt-key", "tauth-key"]

    @model_validator(mode="after")
    def check_external_ids(self: Self) -> Self:
        if self.type == "auth0":
            for field in self.external_ids:
                if field.name == "issuer":
                    if not field.value.startswith("https://"):
                        raise ValueError("Issuer must be an HTTPS URL.")
                    if not field.value.endswith("/"):
                        field.value += "/"
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "auth0": {
                        "summary": "An Auth0 Example",
                        "description": "A **normal** item works correctly.",
                        "value": {
                            "external_ids": [
                                {"name": "issuer", "value": "https://example.com"},
                                {"name": "audience", "value": "example"},
                            ],
                            "extra": [],
                            "organization_name": "org1",
                            "service_name": "service1",
                            "type": "auth0",
                        },
                    },
                },
            ]
        }
    )


class AuthProviderMoreIn(BaseModel):
    external_ids: list[Attribute] = Field(default_factory=list)
    extra: list[Attribute] = Field(default_factory=list)
    organization_ref: OrganizationRef
    service_ref: Optional[ServiceRef]
    type: Literal["auth0", "melt-key", "tauth-key"]


class AuthProviderRef(BaseModel):
    id: PyObjectId = Field(alias="_id")
    organizaion_ref: OrganizationRef
    service_ref: Optional[ServiceRef]
    type: Literal["auth0", "melt-key", "tauth-key"]
