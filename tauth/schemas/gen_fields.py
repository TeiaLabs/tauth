from datetime import datetime

from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from .creator import Creator


class GeneratedFields(BaseModel):
    id: str | PyObjectId = Field(alias="_id")
    created_by: Creator
    created_at: datetime
