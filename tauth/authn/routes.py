from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi import status as s

from ..dependencies.security import RequestAuthenticator
from ..schemas import Infostar

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🪪"])


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authenticate(request: Request) -> Infostar:
    infostar: Infostar = request.state.infostar
    return infostar
