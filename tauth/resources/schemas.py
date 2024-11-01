from typing import Any

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ResourceIn(BaseModel):
    service_handle: str
    role_name: str
    entity_handle: str
    resource_collection: str
    ids: list[str]
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
                            "ids": ["thread-id"],
                            "metadata": {},
                        },
                    },
                },
            ]
        }
    )
