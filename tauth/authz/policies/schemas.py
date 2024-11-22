from typing import Annotated, Literal

from fastapi.openapi.models import Example
from pydantic import AfterValidator, BaseModel

from tauth.entities.schemas import EntityRefIn


class AuthorizationPolicyIn(BaseModel):
    description: str
    name: str
    policy: str
    type: Literal["opa"]


class ResourceAuthorizationRequest(BaseModel):
    service_ref: EntityRefIn
    resource_collection: str


def check_reserved_keys(context: dict):
    reserved_keywords = {
        "infostar",
        "tauth_request",
        "entity",
        "permissions",
        "resources",
    }
    if any(key in reserved_keywords for key in context):
        violations = sorted(reserved_keywords & context.keys())
        raise ValueError(f"Context contains reserved keywords: {violations}")

    return context


Context = Annotated[dict, AfterValidator(lambda x: check_reserved_keys(x))]


class AuthorizationDataIn(BaseModel):
    context: Context
    policy_name: str
    rule: str
    resources: ResourceAuthorizationRequest | None = None


POLICY_EXAMPLES = {
    "opa_melt_key": Example(
        summary="MELT API Key Authorization Policy",
        description="This policy is used to distinguish/authorize MELT API key users.",
        value=dict(
            type="opa",
            name="melt-key",
            description="MELT API Key privilege levels.",
            policy="""
package tauth.melt_key

import rego.v1

default is_valid_user = false
default is_valid_admin = false
default is_valid_superuser = false

is_valid_user := true if {
    input.infostar.authprovider_type == "melt-key"
}

is_valid_admin := true if {
    is_valid_user
    input.infostar.apikey_name == "default"
}

is_valid_superuser := true if {
    is_valid_admin
    input.infostar.authprovider_org == "/"
}
""",
        ),
    )
}
