from typing import Optional, TypedDict

from pydantic import BaseModel, EmailStr
from redbaby.pyobjectid import PyObjectId


class InfostarExtra(TypedDict, total=False):
    geolocation: str
    jwt_sub: str
    os: str
    url: str  # reverse dns
    user_agent: str


class Infostar(BaseModel):
    request_id: PyObjectId  # will be propagated across all services
    apikey_name: str = "jwt"  # specific api key name (nei.workstation.homeoffice)
    authprovider_type: str  # auth0
    authprovider_org: str  # /teialabs
    extra: InfostarExtra
    service_handle: str  # e.g., allai--code
    user_handle: EmailStr  # email
    user_owner_handle: str  # e.g., organization, user family, ...
    client_ip: str
    original: Optional["Infostar"] = None  # if any attributes were overriden
