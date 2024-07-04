from loguru import logger
from opa_client import OpaClient
from opa_client.errors import ConnectionsError, RegoParseError

from ...entities.models import EntityDAO
from ...settings import Settings
from ..policies.models import AuthorizationPolicyDAO
from .interface import AuthorizationInterface


class OPAEngine(AuthorizationInterface):
    def __init__(self):
        logger.debug("Attempting to establish connection with OPA Engine.")
        self.client = OpaClient()
        try:
            self.client.check_connection()
        except ConnectionsError as e:
            logger.error(f"Failed to establish connection with OPA: {e}")
            raise e
        logger.debug("OPA Engine is running.")

    def is_authorized(
        self,
        entity: EntityDAO,
        policy_name: str,
        context: dict,
    ) -> bool:
        opa_context = {"input": context}
        result = self.client.check_permission(
            input_data=opa_context,
            policy_name=policy_name,
            rule_name="is_valid_superuser",
        )

    def get_filters(
        self,
        entity: EntityDAO,
        policy_name: str,
        context: dict,
    ) -> dict:
        raise NotImplementedError

    def upsert_policy(
        self,
        policy_data: AuthorizationPolicyDAO,
    ):
        logger.debug(f"Upserting policy: {policy_data.name}.")
        try:
            self.client.update_opa_policy_fromstring(
                policy_data.policy,
                policy_data.name,
            )
        except RegoParseError as e:
            logger.error(f"Failed to upsert policy in OPA: {e}")
            raise e

    def delete_policy(self, policy_name: str):
        logger.debug(f"Deleting policy: {policy_name}.")
        raise NotImplementedError
