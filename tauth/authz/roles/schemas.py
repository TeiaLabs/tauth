from typing import Optional

from fastapi.openapi.models import Example
from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from ...entities.schemas import EntityRef
from ..permissions.schemas import PermissionOut


class RoleRef(BaseModel):
    id: PyObjectId
    entity: EntityRef


class RoleIn(BaseModel):
    name: str
    description: str
    entity_handle: str
    permissions: Optional[list[str]] = Field(default_factory=list)

    @staticmethod
    def get_role_examples():
        examples = {
            "Role stub": Example(
                description="Simple role with no initial permissions (stub declaration).",
                value=RoleIn(
                    name="api-admin",
                    description="API Administrator",
                    entity_handle="/teialabs",
                ),
            ),
            "Role with permissions": Example(
                description=(
                    "Role declaration with initial permissions. "
                    "The permissions must be created beforehand."
                ),
                value=RoleIn(
                    name="api-admin",
                    description="API Administrator",
                    entity_handle="/teialabs",
                    permissions=["read", "write", "delete"],
                ),
            ),
        }
        return examples


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entity_handle: Optional[str] = None
    permissions: Optional[list[str]] = None

    @staticmethod
    def get_roleupdate_examples():
        examples = {
            "Metadata": Example(
                description="Update role metadata.",
                value=RoleUpdate(
                    name="api-admin",
                    description="API Administrator",
                ),
            ),
            "Update permissions": Example(
                description="Update role permissions (will overwrite existing permissions).",
                value=RoleUpdate(permissions=["read", "write", "delete"]),
            ),
            "Switch entities": Example(
                description="Migrate role to another entity.",
                value=RoleUpdate(entity_handle="/teialabs"),
            ),
        }
        return examples


class RoleIntermediate(BaseModel):
    name: str
    description: str
    entity_ref: EntityRef
    permissions: list[PyObjectId]


class RoleOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    description: str
    entity_handle: str
    permissions: list[PermissionOut]
