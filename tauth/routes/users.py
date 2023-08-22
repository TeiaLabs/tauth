from fastapi import APIRouter, Path, Request

from ..controllers import users as user_controller
from ..schemas import Creator, UserOut

router = APIRouter(prefix="/clients")


@router.get("/{name}/users", status_code=200)
async def read_many(request: Request, name: str = Path(...)) -> list[UserOut]:
    """Read all users from a client."""
    creator: Creator = request.state.creator
    users = user_controller.read_many(client_name=name)
    return users
