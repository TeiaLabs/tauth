import secrets
from hashlib import sha256

from redbaby.pyobjectid import PyObjectId

from tauth.schemas.infostar import Infostar
from tauth.settings import Settings

from .models import TauthTokenDAO
from .schemas import TauthTokenCreationIntermidiate, TauthTokenCreationOut


def hash_value(value: str) -> str:
    salt = Settings.get().SALT

    return sha256(f"{value}{salt}".encode()).hexdigest()


def generate_key_value(
    token_id: PyObjectId,
):
    """
    The tauth key: TAUTH_<db_id>_<secret>
    """
    return f"TAUTH_{str(token_id)}_{secrets.token_hex(32)}"


def create(
    dto: TauthTokenCreationIntermidiate, infostar: Infostar
) -> tuple[TauthTokenDAO, TauthTokenCreationOut]:

    id = PyObjectId()

    secret = generate_key_value(id)

    token_dao = TauthTokenDAO(
        _id=id,
        name=dto.name,
        value_hash=hash_value(secret),
        roles=dto.roles,
        entity=dto.entity,
        created_by=infostar,
    )

    token_out_dto = TauthTokenCreationOut(value=secret, **dto.model_dump())

    return token_dao, token_out_dto
