from typing import Optional

from loguru import logger
from opa_client import OpaClient
from opa_client.errors import ConnectionsError, DeletePolicyError, RegoParseError

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
        resource: str,
        context: Optional[dict] = None,
    ) -> bool:
        opa_context = dict(input={})
        entity_json = entity.model_dump(mode="json")
        opa_context["input"]["entity"] = entity_json
        if context:
            opa_context["input"] |= context
        opa_result = self.client.check_permission(
            input_data=opa_context,
            policy_name=policy_name,
            rule_name=resource,
        )
        logger.debug(f"Raw OPA result: {opa_result}")
        opa_result = opa_result["result"]
        return opa_result

    def get_filters(
        self,
        entity: EntityDAO,
        policy_name: str,
        resource: str,
        context: Optional[dict] = None,
    ) -> dict:
        opa_context = dict(input=dict(context=context, entity=entity))
        opa_result = self.client.check_permission(
            input_data=opa_context,
            policy_name=policy_name,
            rule_name=resource,
        )
        logger.debug(f"Raw OPA result: {opa_result}")
        return opa_result

    def upsert_policy(self, policy_name: str, policy_content: str) -> bool:
        logger.debug(f"Upserting policy {policy_name!r} in OPA.")
        try:
            result = self.client.update_opa_policy_fromstring(
                policy_content,
                policy_name,
            )
        except RegoParseError as e:
            logger.error(f"Failed to upsert policy in OPA: {e}")
            raise e

        if not result:
            logger.error(f"Failed to upsert policy in OPA: {result}")
        return result

    def delete_policy(self, policy_name: str) -> bool:
        logger.debug(f"Deleting policy: {policy_name}.")
        try:
            result = self.client.delete_opa_policy(policy_name)
        except DeletePolicyError as e:
            logger.error(f"Failed to delete policy in OPA: {e}")
            raise e

        if not result:
            logger.error(f"Failed to upsert policy in OPA: {result}")
        return result
