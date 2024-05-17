from typing import Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator
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
                    "melt-api-key": {
                        "summary": "MELT API Key (Teia Labs)",
                        "description": "MELT API Keys of the form `MELT_<organization>/[service]--<key_name>--<key_id>`.",
                        "value": {
                            "organization_name": "/teialabs",
                            # "service_name": "",
                            "type": "melt-key",
                        },
                    },
                    "auth0": {
                        "summary": "Auth0 (Teia Labs)",
                        "description": "Teia Labs' Auth0 as an authprovider.",
                        "value": {
                            "external_ids": [
                                {
                                    "name": "issuer",
                                    "value": "https://dev-z60iog20x0slfn0a.us.auth0.com/",
                                },
                                {
                                    "name": "audience",
                                    "value": "api://allai.chat.webui",
                                },
                            ],
                            "organization_name": "/teialabs",
                            "service_name": "athena-api",
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
