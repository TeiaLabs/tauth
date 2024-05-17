from datetime import datetime

from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from .infostar import Infostar


class GeneratedFields(BaseModel):
    id: str | PyObjectId = Field(alias="_id")
    created_by: Infostar
    created_at: datetime
