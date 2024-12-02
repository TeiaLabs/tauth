from typing import Self

from pydantic import BaseModel

from .infostar import Infostar


class Creator(BaseModel):
    client_name: str
    token_name: str
    user_email: str
    user_ip: str = "127.0.0.1"

    @classmethod
    def from_infostar(cls, infostar: Infostar) -> Self:
        if not infostar.service_handle:
            client_name = infostar.user_owner_handle
        else:
            client_name = (
                f"{infostar.user_owner_handle}/{infostar.service_handle}"
            )
        c = cls(
            client_name=client_name,
            token_name=infostar.apikey_name,
            user_email=infostar.user_handle,
            user_ip=infostar.client_ip,
        )
        return c
