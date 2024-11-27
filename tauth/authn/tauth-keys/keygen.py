import secrets
from hashlib import sha256

from tauth.schemas.infostar import Infostar
from tauth.settings import Settings

from .models import TauthTokenDAO
from .schemas import TauthTokenCreationIntermidiate, TauthTokenCreationOut


def hash_value(value: str) -> str:
    salt = Settings.get().SALT

    return sha256(f"{value}{salt}".encode()).hexdigest()


def generate_key_value(
    token_id: str,
):
    """
    The tauth key: TAUTH/<db_id>/<secret>
    """
    return f"TAUTH/{token_id}/{secrets.token_urlsafe(16)}"


def create(
    dto: TauthTokenCreationIntermidiate, infostar: Infostar
) -> tuple[TauthTokenDAO, TauthTokenCreationOut]:

    token_dao = TauthTokenDAO(
        name=dto.name,
        value_hash="mock",
        roles=dto.roles,
        entity=dto.entity,
        created_by=infostar,
    )

    secret = generate_key_value(token_dao.id)
    token_dao.value_hash = hash_value(secret)

    token_out_dto = TauthTokenCreationOut(value=secret, **dto.model_dump())

    return token_dao, token_out_dto
