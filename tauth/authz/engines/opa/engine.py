from pathlib import Path

from fastapi import HTTPException
from fastapi import status as s
from loguru import logger
from opa_client import OpaClient
from opa_client.errors import (
    ConnectionsError,
    DeletePolicyError,
    PolicyNotFoundError,
    RegoParseError,
)
from redbaby.pyobjectid import PyObjectId

from ....schemas import Infostar
from ...policies.controllers import upsert_one
from ...policies.schemas import AuthorizationPolicyIn
from ..errors import EngineException, PermissionNotFound
from ..interface import AuthorizationInterface, AuthorizationResponse
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
            logger.debug(
                f"Loading policy: {name!r} from {policy_data['path']!r}."
            )
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
        rule: str,
        context: dict | None = None,
        **kwargs,
    ) -> AuthorizationResponse:
        opa_context = dict(input={})
        if context:
            opa_context |= context
        try:
            opa_result = self.client.check_permission(
                input_data=opa_context,
                policy_name=policy_name,
                rule_name=rule,
            )
        except Exception as e:
            logger.error(f"Error in OPA: {e}")
            if isinstance(e, PolicyNotFoundError):
                raise PermissionNotFound(f"Policy {policy_name} not found")
            else:
                raise EngineException(f"Error during authorization check {e}")

        logger.debug(f"Raw OPA result: {opa_result}")
        # TODO: we should be careful here and revisit this soon
        # if the result is an object, the app should check this
        authorized = (
            opa_result["result"]
            if isinstance(opa_result["result"], bool)
            else True
        )
        res = AuthorizationResponse(
            authorized=authorized,
            details=opa_result,
        )
        return res

    def upsert_policy(
        self, policy_name: str, policy_content: str, **_
    ) -> bool:
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
