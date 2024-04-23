from fastapi import APIRouter, Depends, Path, Request

from ..controllers import users as user_controller
from ..injections import privileges
from ..schemas import Creator, UserOut

router = APIRouter(prefix="/clients", tags=["legacy"])


@router.get("/{name}/users", status_code=200)
async def read_many(
    request: Request,
    name: str = Path(...),
    creator: Creator = Depends(privileges.is_valid_user),
) -> list[UserOut]:
    """Read all users from a client."""
    users = user_controller.read_many(client_name=name)
    return users
