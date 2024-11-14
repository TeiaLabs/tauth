from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Unauthorized(Exception):
    """
    Raised when an entity is not authorized to access a resource
    """


class AuthorizationResponse(BaseModel):
    authorized: bool
    details: Any


class AuthorizationInterface(ABC):
    @abstractmethod
    def is_authorized(
        self,
        policy_name: str,
        rule: str,
        context: dict | None = None,
        **kwargs,
    ) -> AuthorizationResponse: ...

    @abstractmethod
    def upsert_policy(
        self,
        policy_name: str,
        policy_content: str,
        **kwargs,
    ) -> bool: ...

    @abstractmethod
    def delete_policy(self, policy_name: str) -> bool: ...
