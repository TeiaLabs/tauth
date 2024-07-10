from fastapi import Depends, HTTPException, Request
from fastapi import status as s
from loguru import logger

from ...authz import privileges
from ...schemas import Infostar
from ...schemas.gen_fields import GeneratedFields
from ...utils import creation, reading
from ..engines.factory import AuthorizationEngine
from ..policies.models import AuthorizationPolicyDAO
from ..policies.schemas import AuthorizationPolicyIn


def create_one(
    body: AuthorizationPolicyIn,
    infostar: Infostar,
) -> GeneratedFields:
    # Insert policy in TAuth's database
    # TODO: use upsert_one
    logger.debug("Inserting policy in TAuth.")
    policy = creation.create_one(body, AuthorizationPolicyDAO, infostar)

    # Insert policy in authorization provider
    logger.debug("Inserting policy in AuthZ provider.")
    authz_engine = AuthorizationEngine.get()
    try:
        result = authz_engine.upsert_policy(
            policy_name=body.name,
            policy_content=body.policy,
        )
    except Exception as e:  # TODO: exception abstraction for authz provider errors
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail=dict(msg=f"Failed to create policy {body.name}: {e}"),
        )
    if not result:
        logger.debug(f"Failed to create policy in authorization engine.")
        authz_policy_col = AuthorizationPolicyDAO.collection()
        result = authz_policy_col.delete_one({"name": body.name})
        logger.debug(f"Deleted objects from TAuth DB: {result.deleted_count}.")
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail=dict(msg=f"Failed to create policy {body.name}."),
        )

    logger.debug(f"Inserted policy in authorization engine.")
    return GeneratedFields(**policy.model_dump(by_alias=True))


def read_many(
    filters: dict,
    infostar: Infostar,
) -> list[AuthorizationPolicyDAO]:
    logger.debug("Reading policies from TAuth.")
    policy = reading.read_many(
        infostar=infostar,
        model=AuthorizationPolicyDAO,
        **filters,
    )
    return policy
