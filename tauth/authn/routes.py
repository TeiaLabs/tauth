from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status as s

from ..dependencies.authentication import authenticate as authenticate_depends
from ..schemas import Infostar

service_name = Path(__file__).parent.name
router = APIRouter(prefix=f"/{service_name}", tags=[service_name + " 🪪"])


@router.post("", status_code=s.HTTP_200_OK)
@router.post("/", status_code=s.HTTP_200_OK, include_in_schema=False)
async def authenticate(
    infostar: Annotated[Infostar, Depends(authenticate_depends)]
) -> Infostar:
    return infostar
