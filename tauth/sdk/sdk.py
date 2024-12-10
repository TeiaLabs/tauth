import httpx

from ..resource_management.access.schemas import GrantIn
from ..resource_management.resources.schemas import ResourceIn
from ..schemas.gen_fields import GeneratedFields


class TAuthClient:
    def __init__(self, api_key: str, url: str):
        self.api_key = api_key
        self.url = url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
        }
        self.http_client = httpx.Client(base_url=url, headers=self.headers)

    def create_resource(self, resource: ResourceIn):
        response = self.http_client.post(
            "/resource_management/resources", json=resource.model_dump()
        )
        response.raise_for_status()
        return GeneratedFields(**response.json())

    def grant_access(self, grant: GrantIn):
        response = self.http_client.post(
            "/resource_management/access/$grant", json=grant.model_dump()
        )
        response.raise_for_status()
        return response.json()
