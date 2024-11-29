import httpx
from fastapi import status as s
from loguru import logger

from tauth.authz.policies.schemas import ResourceAuthorizationRequest

from ..interface import AuthorizationInterface, AuthorizationResponse
from .settings import RemoteSettings


class RemoteEngine(AuthorizationInterface):
    def __init__(self, settings: RemoteSettings):
        self.settings = settings
        self.client = httpx.Client(base_url=self.settings.API_URL)
        logger.debug("Establishing connection with remote AuthZ engine.")
        try:
            self.client.get("/")
        except Exception as e:
            logger.error(
                f"Failed to establish connection with remote AuthZ engine: {e}"
            )
            raise e
        logger.debug("Remote AuthZ engine is running.")

    @staticmethod
    def _get_authorization_header(access_token: str) -> str:
        if access_token.startswith("Bearer"):
            return access_token
        return f"Bearer {access_token}"

    def is_authorized(
        self,
        policy_name: str,
        rule: str,
        access_token: str,
        context: dict | None = None,
        user_email: str | None = None,
        **kwargs,
    ) -> AuthorizationResponse:
        logger.debug(f"Authorizing user using policy {policy_name}")

        headers = {
            "Authorization": self._get_authorization_header(access_token),
            "X-User-Email": user_email,
            "X-Impersonate-Entity-Handle": kwargs.get("impersonate_handle"),
            "X-Impersonate-Entity-Owner": kwargs.get(
                "impersonate_owner_handle"
            ),
        }
        headers = {k: v for k, v in headers.items() if v is not None}
        if context is None:
            context = {}
        body = {
            "context": context,
            "policy_name": policy_name,
            "rule": rule,
        }
        resources = kwargs.get("resources")
        if not resources:
            pass
        else:
            if isinstance(resources, ResourceAuthorizationRequest):
                body["resources"] = resources.model_dump(mode="json")
            elif isinstance(resources, dict):
                body["resources"] = resources
            else:
                cls = ResourceAuthorizationRequest
                cls_path = f"{cls.__module__}.{cls.__name__}"
                raise ValueError(
                    f"Resources should be either {cls_path} or a dictionary."
                )
        body = {k: v for k, v in body.items() if v is not None}
        response = self.client.post("/authz", headers=headers, json=body)
        if response.status_code != s.HTTP_200_OK:
            logger.warning(f"Authorization failed using policy {policy_name}")
            return AuthorizationResponse(
                authorized=False,
                details=response.json(),
            )
        logger.debug(f"Authorization raw response: {response.json()}")
        res = AuthorizationResponse(**response.json())
        if not res.authorized:
            logger.warning(f"Authorization failed using policy {policy_name}")
        else:
            logger.debug(f"Authorization succeeded using policy {policy_name}")
        return res

    def upsert_policy(
        self,
        policy_name: str,
        policy_content: str,
        access_token: str,
        user_email: str | None = None,
        policy_description: str = "",
        **kwargs,
    ) -> bool:
        logger.debug(f"Upserting policy {policy_name!r} remotely.")

        headers = {
            "Authorization": self._get_authorization_header(access_token),
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
        if response.status_code not in (
            s.HTTP_201_CREATED,
            s.HTTP_204_NO_CONTENT,
        ):
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
