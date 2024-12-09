import secrets
from hashlib import sha256

from redbaby.pyobjectid import PyObjectId

from tauth.schemas.infostar import Infostar

from .models import TauthTokenDAO
from .schemas import TauthTokenCreationIntermidiate, TauthTokenCreationOut


def hash_value(value: str) -> str:

    return sha256(value.encode()).hexdigest()


def generate_key_value(token_id: PyObjectId, secret: str):
    """
    The tauth key: TAUTH_<db_id>_<secret>
    """
    return f"TAUTH_{str(token_id)}_{secret}"


def create(
    dto: TauthTokenCreationIntermidiate, infostar: Infostar
) -> tuple[TauthTokenDAO, TauthTokenCreationOut]:

    id = PyObjectId()

    secret = secrets.token_hex(32)

    key = generate_key_value(id, secret)

    token_dao = TauthTokenDAO(
        _id=id,
        name=dto.name,
        value_hash=hash_value(secret),
        roles=dto.roles,
        entity=dto.entity,
        created_by=infostar,
    )

    token_out_dto = TauthTokenCreationOut(value=key, **dto.model_dump())

    return token_dao, token_out_dto
