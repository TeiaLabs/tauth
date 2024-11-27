from pydantic import BaseModel
from redbaby.pyobjectid import PyObjectId

from tauth.entities.schemas import EntityRefIn


class ResourceAccessIn(BaseModel):
    resource_id: PyObjectId
    entity_ref: EntityRefIn


class GrantIn(BaseModel):
    resource_id: PyObjectId
    entity_ref: EntityRefIn
    permission_name: str
