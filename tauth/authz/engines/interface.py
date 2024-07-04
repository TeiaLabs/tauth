from abc import ABC, abstractmethod

from ...entities.models import EntityDAO
from ..policies.models import AuthorizationPolicyDAO


class AuthorizationInterface(ABC):
    @abstractmethod
    def is_authorized(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: dict,
    ) -> bool: ...

    @abstractmethod
    def get_filters(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: dict,
    ) -> dict: ...

    @abstractmethod
    def upsert_policy(
        self,
        policy_data: AuthorizationPolicyDAO,
    ) -> bool: ...

    @abstractmethod
    def delete_policy(self, policy_name: str) -> bool: ...
