from typing import cast

from ...settings import Settings
from .interface import AuthorizationInterface


class AuthorizationEngine:
    _instance: AuthorizationInterface | None = None

    @classmethod
    def setup(cls):
        if cls._instance:
            return
        settings = Settings.get()
        if settings.AUTHZ_ENGINE == "opa":
            from .opa.engine import OPAEngine
            from .opa.settings import OPASettings

            sets = cast(OPASettings, settings.AUTHZ_ENGINE_SETTINGS)
            cls._instance = OPAEngine(settings=sets)
            cls._instance._initialize_db_policies()

        elif settings.AUTHZ_ENGINE == "remote":
            from .remote.engine import RemoteEngine
            from .remote.settings import RemoteSettings

            sets = cast(RemoteSettings, settings.AUTHZ_ENGINE_SETTINGS)
            cls._instance = RemoteEngine(settings=sets)
        else:
            raise Exception("Invalid authz engine")

    @classmethod
    def get(cls) -> AuthorizationInterface:
        if not cls._instance:
            raise Exception("Authz engine not setup")
        return cls._instance
