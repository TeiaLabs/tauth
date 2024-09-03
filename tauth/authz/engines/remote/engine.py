from typing import Optional

from loguru import logger

from ....entities.models import EntityDAO
from ..interface import AuthorizationInterface
from .settings import RemoteSettings


class RemoteEngine(AuthorizationInterface):
    def __init__(self, settings: RemoteSettings):
        self.settings = settings
        pass

    def is_authorized(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: Optional[dict] = None,
    ) -> bool:
        pass

    def get_filters(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: Optional[dict] = None,
    ) -> dict:
        pass

    def upsert_policy(self, policy_name: str, policy_content: str) -> bool:
        pass

    def delete_policy(self, policy_name: str) -> bool:
        pass
