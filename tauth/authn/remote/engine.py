import httpx
from fastapi import HTTPException, Request
from fastapi import status as s
from loguru import logger

from tauth.settings import Settings

from ...schemas import Creator, Infostar


class RequestAuthenticator:
    CLIENT = httpx.Client(base_url=Settings.get().AUTHN_ENGINE_SETTINGS.API_URL)

    @classmethod
    def validate(
        cls,
        request: Request,
        access_token: str,
        id_token: str | None,
        user_email: str | None,
    ):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-ID-Token": id_token,
            "X-User-Email": user_email,
        }
        headers = {k: v for k, v in headers.items() if v is not None}
        print(Settings.get().AUTHN_ENGINE_SETTINGS.API_URL)
        response = cls.CLIENT.post("/authn", headers=headers)
        content = response.json()
        if response.status_code != s.HTTP_200_OK:
            raise HTTPException(status_code=s.HTTP_401_UNAUTHORIZED, detail=content)

        infostar = Infostar(**content)
        request.state.infostar = infostar
        request.state.creator = cls.assemble_creator(infostar)

    @staticmethod
    def assemble_creator(infostar: Infostar) -> Creator:
        logger.debug("Assembling Creator based on Infostar.")
        c = Creator(
            client_name=f"{infostar.user_owner_handle}/{infostar.service_handle}",
            token_name=infostar.apikey_name,
            user_email=infostar.user_handle,
            user_ip=infostar.client_ip,
        )
        return c