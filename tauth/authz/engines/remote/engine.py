from typing import Optional

import httpx
from fastapi import status as s
from loguru import logger

from ..interface import AuthorizationInterface, AuthorizationResponse
from .settings import RemoteSettings


class RemoteEngine(AuthorizationInterface):
    def __init__(self, settings: RemoteSettings):
        self.settings = settings
        self.client = httpx.Client(base_url=self.settings.API_URL)

    def is_authorized(
        self,
        policy_name: str,
        resource: str,
        access_token: str,
        id_token: str | None = None,
        user_email: str | None = None,
        context: Optional[dict] = None,
        **_,
    ) -> AuthorizationResponse:
        logger.debug(f"Authenticating user using policy {policy_name}")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-ID-Token": id_token,
            "X-User-Email": user_email,
        }
        headers = {k: v for k, v in headers.items() if v is not None}
        response = self.client.post("/authn", headers=headers)
        if response.status_code != s.HTTP_200_OK:
            logger.warning(f"Authentication failed using policy {policy_name}")
            return AuthorizationResponse(
                authorized=False,
                filters={},
                details=response.json(),
            )

        logger.debug(f"Authorizing user using policy {policy_name}")
        body = {
            "context": context,
            "policy_name": policy_name,
            "resource": resource,
        }
        body = {k: v for k, v in body.items() if v is not None}
        response = self.client.post("/authz", headers=headers, json=body)
        if response.status_code != s.HTTP_200_OK:
            logger.warning(f"Authorization failed using policy {policy_name}")
            return AuthorizationResponse(
                authorized=False,
                filters={},
                details=response.json(),
            )

        logger.debug(f"Authorization succeeded using policy {policy_name}")
        return AuthorizationResponse(
            authorized=True,
            filters=response.json(),
            details=None,
        )

    def upsert_policy(
        self,
        policy_name: str,
        policy_content: str,
        access_token: str,
        id_token: str | None = None,
        user_email: str | None = None,
        policy_description: str = "",
    ) -> bool:
        logger.debug(f"Upserting policy {policy_name!r} remotely.")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-ID-Token": id_token,
            "X-User-Email": user_email,
        }
        headers = {k: v for k, v in headers.items() if v is not None}
        body = {
            "type": "opa",
            "name": policy_name,
            "description": policy_description,
            "policy": policy_content,
        }
        response = self.client.put(
            "/authz/policies",
            headers=headers,
            json=body,
        )
        if response.status_code not in (s.HTTP_201_CREATED, s.HTTP_204_NO_CONTENT):
            details = response.json()
            logger.warning(f"Failed to upsert policy remotely: {details}")
            return False
        return True

    def delete_policy(self, policy_name: str) -> bool:
        logger.debug(f"Deleting policy {policy_name!r} remotely.")
        response = self.client.delete(
            f"/authz/policies/{policy_name}",
        )
        if response.status_code != s.HTTP_204_NO_CONTENT:
            details = response.json()
            logger.warning(f"Failed to delete policy remotely: {details}")
            return False
        return True
