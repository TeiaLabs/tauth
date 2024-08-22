from typing import Optional

from fastapi.openapi.models import Example
from pydantic import BaseModel, Field

from ..entities.models import EntityRef
from .utils import UniqueOrderedList


class RoleIn(BaseModel):
    name: str
    description: str
    entity_handle: str
    permissions: Optional[UniqueOrderedList] = Field(default_factory=list)

    @staticmethod
    def get_rolein_examples():
        examples = {
            "Simple role": Example(
                description=(
                    "Simple role declaration with one permission (role name). "
                    "Use this if you want to create a role with a single permission."
                ),
                value=RoleIn(
                    name="api-admin",
                    description="API Administrator",
                    entity_handle="/teialabs",
                ),
            ),
            "Role with multiple permissions": Example(
                description=(
                    "Role declaration with multiple permissions. "
                    "Use this if you want to create a role with multiple permissions."
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
    permissions: Optional[UniqueOrderedList] = None


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
    permissions: list[str]
