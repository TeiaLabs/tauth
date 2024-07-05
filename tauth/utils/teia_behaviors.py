from pydantic import BaseModel

from ..schemas import Infostar


class Authoring(BaseModel):
    created_by: Infostar
