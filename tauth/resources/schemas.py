from typing import Any

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from tauth.entities.schemas import EntityRef

from ..authz.permissions.schemas import PermissionContext


class Identifier(BaseModel):
    id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourceIn(BaseModel):
    service_handle: str
    role_name: str
    entity_handle: str
    resource_collection: str
    ids: list[Identifier]
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "shared-thread": {
                        "summary": "Shared Thread",
                        "description": "Thread shared between users",
                        "value": {
                            "service_handle": "/athena-api",
                            "role_name": "share_thread",
                            "entity_handle": "/my-group",
                            "resource_collection": "threads",
                            "ids": [
                                {
                                    "id": "thread-id",
                                    "metadata": {"alias": "osf"},
                                }
                            ],
                        },
                    },
                },
            ]
        }
    )


class ResourceUpdate(BaseModel):
    append_ids: list[Identifier] | None = Field(None)
    remove_ids: list[str] | None = Field(None)
    metadata: dict[str, Any] | None = Field(None)


class ResourceContext(BaseModel):
    service_ref: EntityRef
    permissions: list[PermissionContext]
    resource_collection: str
    ids: list[Identifier]
    metadata: dict[str, Any]