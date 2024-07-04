from typing import Literal

from pydantic import BaseModel


class AuthorizationPolicyIn(BaseModel):
    name: str
    policy: str
    type: Literal["opa"]


class AuthorizationDataIn(BaseModel):
    resource: str
    policy_name: str
    context: dict
