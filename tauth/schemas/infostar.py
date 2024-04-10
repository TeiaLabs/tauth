from typing import Optional

from pydantic import BaseModel, EmailStr


class Infostar(BaseModel):
    client_name: str  # /osf/allai/code/extension
    extra: dict[str, str]  # e.g.: user-agent,
    human: bool  # differentiates between machine and human users
    org_name: str  # /teialabs
    original: Optional["Infostar"]  # if any attributes were overriden
    token_name: str  # nei.workstation.homeoffice
    user_email: EmailStr  # nei@teialabs.com
    user_ip: str  # 170.0.0.69
