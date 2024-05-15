from fastapi import APIRouter, Depends, Path, Request
from loguru import logger

from ..auth.melt_key.schemas import UserOut
from ..entities.models import EntityDAO
from ..injections import privileges
from ..schemas import Creator
from ..utils import reading

router = APIRouter(prefix="/clients", tags=["legacy"])


@router.get("/{name}/users", status_code=200)
async def read_many(
    request: Request,
    name: str = Path(...),
    creator: Creator = Depends(privileges.is_valid_user),
) -> list[UserOut]:
    """Read all users from a client."""
    logger.info(f"Reading all users from client {name!r}.")
    filters = {"type": "user", "owner_ref.handle": name}
    items = reading.read_many(creator={}, model=EntityDAO, **filters)
    users = [
        UserOut(
            created_at=i.created_at,
            created_by=i.created_by,
            email=i.handle,
        )
        for i in items
    ]
    return users