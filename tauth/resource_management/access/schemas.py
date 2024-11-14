from pydantic import BaseModel
from redbaby.pyobjectid import PyObjectId

from tauth.authz.permissions.schemas import PermissionIn


class ResourceAccessIn(BaseModel):
    resource_id: PyObjectId
    entity_handle: str

class GrantIn(BaseModel):
    resource_id: PyObjectId
    entity_handle: str
    permission: PermissionIn