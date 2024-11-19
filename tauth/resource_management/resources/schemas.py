from typing import Any

from fastapi.openapi.models import Example
from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from tauth.entities.schemas import EntityRef, EntityRefIn


class Identifier(BaseModel):
    id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResourceIn(BaseModel):
    service_ref: EntityRefIn
    resource_collection: str
    ids: list[Identifier]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def get_resource_in_examples():
        examples = {
            "shared-thread": Example(
                description="Thread shared between users",
                value=ResourceIn(
                    service_ref=EntityRefIn(handle="/athena-api"),
                    resource_collection="threads",
                    ids=[
                        Identifier(id="thread-id", metadata={"alias": "osf"})
                    ],
                ),
            )
        }
        return examples


class ResourceUpdate(BaseModel):
    append_ids: list[Identifier] | None = Field(None)
    remove_ids: list[str] | None = Field(None)
    metadata: dict[str, Any] | None = Field(None)


class ResourceContext(BaseModel):
    id: PyObjectId = Field(alias="_id")
    service_ref: EntityRef
    resource_collection: str
    ids: list[Identifier]
    metadata: dict[str, Any]
