from typing import Literal

from pydantic import BaseModel


class AuthorizationPolicyIn(BaseModel):
    description: str
    name: str
    policy: str
    type: Literal["opa"]


class AuthorizationDataIn(BaseModel):
    context: dict
    policy_name: str
    resource: str


from fastapi.openapi.models import Example

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
