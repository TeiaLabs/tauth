from datetime import datetime

from pydantic import BaseModel, Field

from ..schemas import Creator


class GeneratedFields(BaseModel):
    id: str = Field(alias="_id")
    created_by: Creator
    created_at: datetime
