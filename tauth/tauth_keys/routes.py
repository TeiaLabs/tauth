from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import status as s
from loguru import logger
from redbaby.pyobjectid import PyObjectId

from tauth.authn.tauth_keys.schemas import TauthTokenDTO
from tauth.entities.models import EntityDAO
from tauth.settings import Settings

from ..authn.tauth_keys.keygen import create
from ..authn.tauth_keys.models import TauthTokenDAO
from ..authn.tauth_keys.schemas import (
    TauthTokenCreationIn,
    TauthTokenCreationIntermidiate,
)
from ..authz.privileges import is_valid_admin
from ..dependencies.authentication import authenticate
from ..schemas.infostar import Infostar
from ..utils import reading

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🪙"])


@router.post("", status_code=s.HTTP_201_CREATED)
async def create_one(
    body: TauthTokenCreationIn = Body(),
    infostar: Infostar = Depends(authenticate),
):
    logger.debug(f"Creating tauth-token for {infostar}")
    entity = EntityDAO.from_handle(
        body.entity.handle, body.entity.owner_handle
    )

    if not entity:
        raise HTTPException(s.HTTP_404_NOT_FOUND, detail="entity not found")

    tauth_token_intermidiate = TauthTokenCreationIntermidiate(
        entity=entity.to_ref(), **body.model_dump(exclude={"entity"})
    )

    token_dao, token_out = create(tauth_token_intermidiate, infostar)

    coll = TauthTokenDAO.collection(alias=Settings.get().REDBABY_ALIAS)

    coll.insert_one(token_dao.model_dump(by_alias=True))

    return token_out


@router.get("/{token_id}")
async def read_one(
    token_id: str, infostar: Infostar = Depends(authenticate)
) -> TauthTokenDTO:
    token = reading.read_one_filters(
        infostar=infostar,
        model=TauthTokenDAO,
        _id=PyObjectId(token_id),
        deleted=False,
    )

    return token.to_dto()


@router.delete("/{token_id}", status_code=s.HTTP_204_NO_CONTENT)
async def delete_one(
    token_id: str, infostar: Infostar = Depends(is_valid_admin)
):
    logger.debug(f"Deleting tauth-token: {token_id}")
    coll = TauthTokenDAO.collection(alias=Settings.get().REDBABY_ALIAS)

    res = coll.update_one(
        {"_id": PyObjectId(token_id)}, {"$set": {"deleted": True}}
    )

    if res.matched_count == 0:
        raise HTTPException(s.HTTP_404_NOT_FOUND, detail="token not found")
    if res.modified_count == 0:
        raise HTTPException(
            s.HTTP_422_UNPROCESSABLE_ENTITY, detail="token was already deleted"
        )
