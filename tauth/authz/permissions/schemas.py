from fastapi.openapi.models import Example
from pydantic import BaseModel
from redbaby.pyobjectid import PyObjectId

from ...entities.schemas import EntityRef


class PermissionIn(BaseModel):
    name: str
    description: str
    entity_handle: str

    @staticmethod
    def get_permission_create_examples():
        examples = {
            "Resource read access": Example(
                description="Adds read access to a specific resource.",
                value=PermissionIn(
                    name="resource-read",
                    description="Resource read access.",
                    entity_handle="/teialabs",
                ),
            ),
            "API admin access": Example(
                description="Role declaration with multiple permissions. ",
                value=PermissionIn(
                    name="api-admin",
                    description="API administrator access.",
                    entity_handle="/teialabs",
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
    entity_handle: str | None = None

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
                value=PermissionUpdate(entity_handle="/teialabs"),
            ),
        }
        return examples


class PermissionIntermediate(BaseModel):
    name: str
    description: str
    entity_ref: EntityRef


class PermissionContext(BaseModel):
    name: str
    entity_handle: str
    role_id: PyObjectId
