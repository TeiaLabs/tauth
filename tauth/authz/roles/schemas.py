from fastapi.openapi.models import Example
from pydantic import BaseModel, Field
from redbaby.pyobjectid import PyObjectId

from ...entities.schemas import EntityRef, EntityRefIn
from ..permissions.schemas import PermissionOut


class RoleRef(BaseModel):
    id: PyObjectId


class RoleIn(BaseModel):
    name: str
    description: str
    entity_ref: EntityRefIn
    permissions: list[str] | None = Field(default_factory=list)

    @staticmethod
    def get_role_examples():
        examples = {
            "Role stub": Example(
                description="Simple role with no initial permissions (stub declaration).",
                value=RoleIn(
                    name="api-admin",
                    description="API Administrator",
                    entity_ref=EntityRefIn(handle="/teialabs"),
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
                    entity_ref=EntityRefIn(handle="/teialabs"),
                    permissions=["read", "write", "delete"],
                ),
            ),
        }
        return examples


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    entity_handle: EntityRefIn | None = None
    permissions: list[str] | None = None

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
                value=RoleUpdate(
                    entity_handle=EntityRefIn(handle="/teialabs")
                ),
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
