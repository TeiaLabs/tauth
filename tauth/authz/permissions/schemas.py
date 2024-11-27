from typing import Any

from fastapi.openapi.models import Example
from pydantic import BaseModel

from ...entities.schemas import EntityRef, EntityRefIn
from .models import PermissionType


class PermissionIn(BaseModel):
    name: str
    description: str
    entity_ref: EntityRefIn
    type: PermissionType

    @staticmethod
    def get_permission_create_examples():
        examples = {
            "Resource read access": Example(
                description="Adds read access to a specific resource.",
                value=PermissionIn(
                    name="resource-read",
                    description="Resource read access.",
                    entity_ref=EntityRefIn(handle="/teialabs"),
                    type="resource",
                ),
            ),
            "API admin access": Example(
                description="Role declaration with multiple permissions. ",
                value=PermissionIn(
                    name="api-admin",
                    description="API administrator access.",
                    entity_ref=EntityRefIn(handle="/teialabs"),
                    type="generic",
                ),
            ),
        }
        return examples


class PermissionOut(BaseModel):
    name: str
    description: str
    entity_ref: EntityRef


class PermissionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    entity_ref: EntityRefIn | None = None

    @staticmethod
    def get_permission_update_examples():
        examples = {
            "Metadata": Example(
                description="Update permission metadata.",
                value=PermissionUpdate(
                    name="api-admin",
                    description="API Administrator",
                ),
            ),
            "Switch entities": Example(
                description="Migrate permission to another entity.",
                value=PermissionUpdate(
                    entity_ref=EntityRefIn(handle="/teialabs")
                ),
            ),
        }
        return examples


class PermissionIntermediate(BaseModel):
    name: str
    description: str
    entity_ref: EntityRef
    type: PermissionType


class PermissionContext(BaseModel):
    name: str
    entity_handle: str

    def __hash__(self):
        return hash((self.name, self.entity_handle))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PermissionContext):
            # Equality based on name and entity_handle
            return (self.name, self.entity_handle) == (
                other.name,
                other.entity_handle,
            )
        return False
