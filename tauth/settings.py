from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .authn import remote as authn_remote
from .authz.engines import opa as authz_opa
from .authz.engines import remote as authz_remote


class Settings(BaseSettings):
    # API
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    RELOAD: bool = False
    WORKERS: int = 1

    # Database
    MONGODB_DBNAME: str = "tauth"
    MONGODB_URI: str = "mongodb://localhost:27017/"
    REDBABY_ALIAS: str = "tauth"

    # Security
    ROOT_API_KEY: str = "MELT_/--default--1"
    AUTHN_ENGINE: Literal["database", "remote"]
    AUTHZ_ENGINE: Literal["opa", "remote"]

    @computed_field
    @property
    def AUTHN_ENGINE_SETTINGS(self) -> authn_remote.RemoteSettings:
        return authn_remote.RemoteSettings()

    @computed_field
    @property
    def AUTHZ_ENGINE_SETTINGS(
        self,
    ) -> authz_opa.OPASettings | authz_remote.RemoteSettings:
        if self.AUTHZ_ENGINE == "opa":
            return authz_opa.OPASettings()
        elif self.AUTHZ_ENGINE == "remote":
            return authz_remote.RemoteSettings()  # type: ignore
        else:
            raise ValueError("Invalid AUTHZ_ENGINE_SETTINGS value")

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_prefix="TAUTH_",
    )

    @classmethod
    @lru_cache(maxsize=1)
    def get(cls):
        return cls()
