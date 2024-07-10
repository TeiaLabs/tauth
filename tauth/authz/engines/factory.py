from ...settings import Settings
from .interface import AuthorizationInterface
from .opa import OPAEngine


class AuthorizationEngine:
    _instance: AuthorizationInterface | None = None

    @classmethod
    def get(cls) -> AuthorizationInterface:
        if not cls._instance:
            # settings = Settings.get()
            cls._instance = OPAEngine()
        return cls._instance
