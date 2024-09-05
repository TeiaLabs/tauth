from fastapi import Depends, Header, Request
from redbaby.database import DB
from redbaby.document import Document

from tauth.authz.engines.factory import AuthorizationEngine
from tauth.authz.engines.interface import AuthorizationResponse
from tauth.dependencies.security import RequestAuthenticator


def setup_database(dbname: str, dburi: str, redbaby_alias: str):
    DB.add_conn(
        db_name=dbname,
        uri=dburi,
        alias=redbaby_alias,
    )
    for m in Document.__subclasses__():
        if m.__module__.startswith("tauth"):
            m.create_indexes(alias=redbaby_alias)


def get_depends():
    return Depends(RequestAuthenticator.validate)


def policy_authorizer(policy_name: str, base_context: dict | None = None):
    def resource_authorizer(
        resource: str,
        context: dict | None = None,
    ):
        def wrap(
            access_token: str = Header(alias="Authorization"),
            id_token: str | None = Header(None, alias="X-ID-Token"),
            user_email: str | None = Header(None, alias="X-User-Email"),
        ):
            AuthorizationEngine.setup()
            engine = AuthorizationEngine.get()
            actual_context = None
            if base_context is not None:
                actual_context = base_context
                if context is not None:
                    actual_context.update(context)
            elif context is not None:
                actual_context = context

            return engine.is_authorized(
                policy_name=policy_name,
                resource=resource,
                access_token=access_token,
                id_token=id_token,
                user_email=user_email,
                context=actual_context,
                entity=None,  # type: ignore
            )

        return Depends(wrap)

    return resource_authorizer


def authorize(
    policy_name: str,
    resource: str,
    context: dict | None = None,
):
    def authorize(
        access_token: str = Header(alias="authorization"),
        id_token: str | None = Header(None, alias="x-id-token"),
        user_email: str | None = Header(None, alias="x-user-email"),
    ) -> AuthorizationResponse:
        AuthorizationEngine.setup()
        engine = AuthorizationEngine.get()
        return engine.is_authorized(
            policy_name=policy_name,
            resource=resource,
            access_token=access_token,
            id_token=id_token,
            user_email=user_email,
            context=context,
            entity=None,  # type: ignore
        )

    return Depends(authorize)
