from pathlib import Path

from fastapi import HTTPException
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from ..authz.engines.factory import AuthorizationEngine
from ..authz.policies.controllers import create_one
from ..authz.policies.schemas import AuthorizationPolicyIn
from ..schemas import Infostar

DEFAULT_POLICIES = {
    "melt-key": Path(__file__).parents[2] / "resources" / "policies" / "melt-key.rego"
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


def init_app():
    logger.debug("Initializing policy engine.")
    authz_engine = AuthorizationEngine.get()  # caching
    # TODO: maybe move this to authz engine
    for name, policy_path in DEFAULT_POLICIES.items():
        logger.debug(f"Loading policy: {name} from {policy_path}.")
        policy_content = policy_path.read_text()
        policy = AuthorizationPolicyIn(name=name, policy=policy_content, type="opa")
        try:
            create_one(policy, SYSTEM_INFOSTAR)
        except HTTPException as e:
            if e.status_code != s.HTTP_409_CONFLICT:
                raise e
            logger.debug(f"Policy {name} already exists. Skipping.")

    logger.debug("Policy engine initialized.")
