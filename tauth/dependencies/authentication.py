from fastapi import APIRouter, Depends, FastAPI, Request

from tauth.authn.authenticator import _authenticate
from tauth.schemas.infostar import Infostar


def init_app(app: FastAPI):
    app.router.dependencies.append(Depends(_authenticate, use_cache=True))


def init_router(router: APIRouter):
    router.dependencies.append(Depends(_authenticate, use_cache=True))


def authenticate(request: Request, _=Depends(_authenticate)) -> Infostar:
    infostar: Infostar = request.state.infostar
    return infostar
