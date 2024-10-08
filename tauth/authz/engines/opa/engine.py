from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from fastapi import status as s
from loguru import logger
from opa_client import OpaClient
from opa_client.errors import ConnectionsError, DeletePolicyError, RegoParseError
from redbaby.pyobjectid import PyObjectId

from ....entities.models import EntityDAO
from ....schemas import Infostar
from ...policies.controllers import upsert_one
from ...policies.schemas import AuthorizationPolicyIn
from ..interface import AuthorizationInterface
from .settings import OPASettings

PATH_POLICIES = Path(__file__).parents[4] / "resources" / "policies"

DEFAULT_POLICIES = {
    "melt-key": {
        "path": PATH_POLICIES / "melt-key.rego",
        "description": "MELT API Key privilege levels.",
    },
}

SYSTEM_INFOSTAR = Infostar(
    request_id=PyObjectId(),
    apikey_name="default",
    authprovider_org="/",
    authprovider_type="melt-key",
    extra={},
    service_handle="tauth",
    user_handle="sysadmin@teialabs.com",
    user_owner_handle="/",
    original=None,
    client_ip="127.0.0.1",
)


class OPAEngine(AuthorizationInterface):
    def __init__(self, settings: OPASettings):
        self.settings = settings
        logger.debug("Attempting to establish connection with OPA Engine.")
        self.client = OpaClient(host=settings.HOST, port=settings.PORT)
        try:
            self.client.check_connection()
        except ConnectionsError as e:
            logger.error(f"Failed to establish connection with OPA: {e}")
            raise e
        logger.debug("OPA Engine is running.")

    def _initialize_default_policies(self):
        logger.debug("Inserting default policies")
        for name, policy_data in DEFAULT_POLICIES.items():
            logger.debug(f"Loading policy: {name!r} from {policy_data['path']!r}.")
            policy_content = policy_data["path"].read_text()
            policy = AuthorizationPolicyIn(
                name=name,
                description=policy_data["description"],
                policy=policy_content,
                type="opa",
            )
            try:
                upsert_one(policy, SYSTEM_INFOSTAR)
            except HTTPException as e:
                if e.status_code != s.HTTP_409_CONFLICT:
                    raise e
                logger.debug(f"Policy {name} already exists. Skipping.")

    def is_authorized(
        self,
        policy_name: str,
        resource: str,
        entity: EntityDAO,
        context: Optional[dict] = None,
        **_,
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

    def upsert_policy(self, policy_name: str, policy_content: str) -> bool:
        logger.debug(f"Upserting policy {policy_name!r} in OPA.")
        try:
            result = self.client.update_policy_from_string(
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
            result = self.client.delete_policy(policy_name)
        except DeletePolicyError as e:
            logger.error(f"Failed to delete policy in OPA: {e}")
            raise e

        if not result:
            logger.error(f"Failed to upsert policy in OPA: {result}")
        return result
