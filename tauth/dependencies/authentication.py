from fastapi import APIRouter, Depends, FastAPI, Request

from tauth.authn.authenticator import authn
from tauth.schemas.infostar import Infostar


def init_app(app: FastAPI):
    app.router.dependencies.append(Depends(authn(), use_cache=True))


def init_router(router: APIRouter):
    router.dependencies.append(Depends(authn(), use_cache=True))


def authenticate(request: Request, _=Depends(authn())) -> Infostar:
    try:
        infostar: Infostar = request.state.infostar
    except AttributeError:
        raise AttributeError(
            "Infostar not found in request.state. Check authn ignored paths"
        )
    return infostar
