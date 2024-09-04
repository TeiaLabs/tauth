from abc import ABC, abstractmethod
from typing import Any, Optional

from ...entities.models import EntityDAO


class Unauthorized(Exception):
    """
    Raised when an entity is not authorized to access a resource
    """


class AuthorizationResponse:
    def __init__(self, authorized: bool, filters: dict, details: Any) -> None:
        self.authorized = authorized
        self.details = details
        self.__filters = filters

    @property
    def filters(self) -> dict:
        if self.authorized:
            return self.__filters

        raise Unauthorized()


class AuthorizationInterface(ABC):
    @abstractmethod
    def is_authorized(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: Optional[dict] = None,
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
