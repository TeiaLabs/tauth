from fastapi import APIRouter, Depends, FastAPI

from ..authn.authenticator import RequestAuthenticator


def get_depends():
    return Depends(RequestAuthenticator.validate)


def init_app(app: FastAPI):
    app.router.dependencies.append(get_depends())


def init_router(router: APIRouter):
    router.dependencies.append(get_depends())
