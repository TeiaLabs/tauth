from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, EmailStr
from redbaby.pyobjectid import PyObjectId

from ..authproviders.schemas import AuthProviderRef


class InfostarExtra(TypedDict, total=False):
    geolocation: str
    jwt_sub: str
    os: str  # reverse dns
    url: str
    user_agent: str


class Infostar(BaseModel):
    request_id: PyObjectId  # will be propagated across all services
    auth_token_name: str  # JWT generic name (e.g., osf-auth0) or specific api key name (nei.workstation.homeoffice)
    authprovider_ref: AuthProviderRef  # {id, organizaion_ref, service_ref, type}
    extra: InfostarExtra
    app_name: str  # e.g., /osf/allai/code
    user_email: EmailStr  # email
    user_owner: str  # e.g., organization, user family, ...
    client_ip: str

    original: Optional["Infostar"]  # if any attributes were overriden
