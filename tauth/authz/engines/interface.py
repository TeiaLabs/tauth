from abc import ABC, abstractmethod
from typing import Optional

from ...entities.models import EntityDAO


class AuthorizationInterface(ABC):
    @abstractmethod
    def is_authorized(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: Optional[dict] = None,
    ) -> bool: ...

    @abstractmethod
    def get_filters(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: Optional[dict] = None,
    ) -> dict: ...

    @abstractmethod
    def upsert_policy(self, policy_name: str, policy_content: str) -> bool: ...

    @abstractmethod
    def delete_policy(self, policy_name: str) -> bool: ...
