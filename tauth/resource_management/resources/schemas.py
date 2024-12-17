from typing import Any

from fastapi.openapi.models import Example
from pydantic import BaseModel, Field

from tauth.entities.schemas import EntityRefIn


class ResourceIn(BaseModel):
    service_ref: EntityRefIn
    resource_collection: str
    resource_identifier: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def get_resource_in_examples():
        examples = {
            "shared-thread": Example(
                description="Thread shared between users",
                value=ResourceIn(
                    service_ref=EntityRefIn(handle="/athena-api"),
                    resource_collection="threads",
                    resource_identifier="thread_id_1245",
                    metadata={"alias": "osf"},
                ),
            )
        }
        return examples


class ResourceUpdate(BaseModel):
    metadata: dict[str, Any]
