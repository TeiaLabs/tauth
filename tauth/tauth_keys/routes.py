from pathlib import Path

from fastapi import APIRouter
from fastapi import status as s
from redbaby.pyobjectid import PyObjectId

from tauth.authn.tauth_keys.schemas import TauthTokenDTO

from ..authn.tauth_keys.models import TauthTokenDAO
from ..utils import reading

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🪙"])


@router.post("", status_code=s.HTTP_201_CREATED)
async def create_one():
    pass


@router.get("/{id}")
async def read_one(entity_id: str) -> TauthTokenDTO:
    token = reading.read_one_filters(
        infostar={},  # type: ignore
        model=TauthTokenDAO,
        identifier=PyObjectId(entity_id),
        deleted=False,
    )

    return token.to_dto()


@router.delete("/{id}", status_code=s.HTTP_204_NO_CONTENT)
async def delete_one(entity_id: str):
    pass
