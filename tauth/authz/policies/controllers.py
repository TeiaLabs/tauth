from fastapi import HTTPException
from fastapi import status as s
from loguru import logger

from ...schemas import Infostar
from ...schemas.gen_fields import GeneratedFields
from ...settings import Settings
from ...utils import creation, reading
from ..engines.factory import AuthorizationEngine
from ..policies.models import AuthorizationPolicyDAO
from ..policies.schemas import AuthorizationPolicyIn


def upsert_one(
    body: AuthorizationPolicyIn,
    infostar: Infostar,
) -> GeneratedFields:
    # Insert policy in TAuth's database
    logger.debug("Inserting policy in TAuth.")
    policy_col = AuthorizationPolicyDAO.collection(
        alias=Settings.get().TAUTH_REDBABY_ALIAS
    )
    policy_content = body.model_dump(by_alias=True) | {
        "created_by": infostar.model_dump()
    }
    result = policy_col.update_one(
        {"name": body.name},
        {"$set": policy_content},
        upsert=True,
    )
    logger.debug(f"Policy upsert result: {result}.")
    policy = AuthorizationPolicyDAO(**policy_content)

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
            detail=dict(msg=f"Failed to create policy {body.name!r} in engine: {e}"),
        )
    if not result:
        logger.debug(f"Failed to create policy in authorization engine.")
        authz_policy_col = AuthorizationPolicyDAO.collection()
        result = authz_policy_col.delete_one({"name": body.name})
        logger.debug(f"Deleted objects from TAuth DB: {result.deleted_count}.")
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail=dict(msg=f"Failed to create policy {body.name!r} in engine."),
        )

    logger.debug(f"Inserted policy in authorization engine.")
    return GeneratedFields(**policy.model_dump(by_alias=True))


def read_one(id: str) -> AuthorizationPolicyDAO:
    logger.debug("Reading policy from TAuth.")
    policy = reading.read_one(
        infostar={},  # type: ignore
        model=AuthorizationPolicyDAO,
        identifier=id,
    )
    print(type(policy))
    return policy


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


def delete_one(id: str) -> None:
    logger.debug("Deleting policy from TAuth.")
    policy = reading.read_one(
        infostar={},  # type: ignore
        model=AuthorizationPolicyDAO,
        identifier=id,
    )
    policy_col = AuthorizationPolicyDAO.collection()
    result = policy_col.delete_one({"name": policy.name})
    logger.debug(f"Deleted objects from TAuth DB: {result.deleted_count}.")

    logger.debug("Deleting policy from AuthZ provider.")
    authz_engine = AuthorizationEngine.get()
    try:
        result = authz_engine.delete_policy(
            policy_name=policy.name,
        )
    except Exception as e:  # TODO: exception abstraction for authz provider errors
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail=dict(msg=f"Failed to delete policy {policy.name!r} in engine: {e}"),
        )
    if not result:
        logger.debug(f"Failed to delete policy in authorization engine.")
        raise HTTPException(
            status_code=s.HTTP_400_BAD_REQUEST,
            detail=dict(msg=f"Failed to delete policy {policy.name!r} in engine."),
        )
    logger.debug(f"Deleted policy from authorization engine.")
