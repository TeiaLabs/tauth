from typing import cast

from ...settings import Settings
from .interface import AuthorizationInterface
from .opa.engine import OPAEngine
from .opa.settings import OPASettings
from .remote.engine import RemoteEngine
from .remote.settings import RemoteSettings


class AuthorizationEngine:
    _instance: AuthorizationInterface | None = None

    @classmethod
    def setup(cls):
        settings = Settings.get()
        if settings.AUTHZ_ENGINE == "opa":
            sets = cast(OPASettings, settings.AUTHZ_ENGINE_SETTINGS)
            cls._instance = OPAEngine(settings=sets)
        elif settings.AUTHZ_ENGINE == "remote":
            sets = cast(RemoteSettings, settings.AUTHZ_ENGINE_SETTINGS)
            cls._instance = RemoteEngine(settings=sets)
        else:
            raise Exception("Invalid authz engine")

    @classmethod
    def get(cls) -> AuthorizationInterface:
        if not cls._instance:
            raise Exception("Authz engine not setup")
        return cls._instance
