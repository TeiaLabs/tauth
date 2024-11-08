from pydantic import BaseModel
from redbaby.pyobjectid import PyObjectId


class ResourceAccessIn(BaseModel):
    resource_id: PyObjectId
    entity_handle: str
