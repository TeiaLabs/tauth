from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .authz.engines.opa.settings import OPASettings
from .authz.engines.remote.settings import RemoteSettings


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
    AUTHZ_ENGINE: Literal["opa", "remote"] = "opa"

    @computed_field
    @property
    def AUTHZ_ENGINE_SETTINGS(self) -> OPASettings | RemoteSettings:
        if self.AUTHZ_ENGINE == "opa":
            return OPASettings()
        elif self.AUTHZ_ENGINE == "remote":
            return RemoteSettings()  # type: ignore
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
