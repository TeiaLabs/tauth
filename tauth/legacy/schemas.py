from pydantic import BaseModel


class MeltAPIKeyIn(BaseModel):
    name: str
    organization_handle: str
    service_handle: str