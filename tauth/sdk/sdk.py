from collections.abc import Iterable
from copy import deepcopy

import httpx

from ..authz.engines.interface import AuthorizationResponse
from ..authz.permissions.models import PermissionDAO
from ..authz.policies.schemas import AuthorizationDataIn
from ..resource_management.access.schemas import GrantIn, GrantResponse
from ..resource_management.resources.schemas import ResourceIn
from ..schemas.gen_fields import GeneratedFields


class TAuthClient:
    def __init__(self, api_key: str, url: str):
        self.api_key = api_key
        self.url = url.removesuffix("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
        }
        self.http_client = httpx.Client(base_url=url, headers=self.headers)

    def create_resource(self, resource: ResourceIn) -> GeneratedFields:
        response = self.http_client.post(
            "/resource_management/resources", json=resource.model_dump()
        )
        response.raise_for_status()
        return GeneratedFields(**response.json())

    def grant_access(self, grant: GrantIn) -> GrantResponse:
        response = self.http_client.post(
            "/resource_management/access/$grant",
            json=grant.model_dump(mode="json"),
        )
        response.raise_for_status()
        return GrantResponse(**response.json())

    def delete_permission(self, permission_id: str) -> int:
        response = self.http_client.delete(f"/authz/permissions/{permission_id}")
        response.raise_for_status()
        return response.status_code

    def read_permissions(self, params: dict) -> Iterable[PermissionDAO]:
        response = self.http_client.get("/authz/permissions", params=params)
        response.raise_for_status()
        perms = response.json()
        return map(lambda x: PermissionDAO(**x), perms)

    def delete_resource(self, resource_id: str) -> int:
        response = self.http_client.delete(
            f"/resource_management/resources/{resource_id}"
        )
        response.raise_for_status()
        return response.status_code
