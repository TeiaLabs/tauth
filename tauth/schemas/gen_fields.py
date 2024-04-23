from datetime import datetime

from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from ..schemas import Creator


class GeneratedFields(BaseModel):
    id: str | PyObjectId = Field(alias="_id")
    created_by: Creator
    created_at: datetime
