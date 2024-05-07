from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # uvicorn
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    RELOAD: bool = False
    WORKERS: int = 1

    # MELT API key
    TAUTH_ROOT_API_KEY: str = "MELT_/--default--1"

    # mongodb
    TAUTH_MONGODB_DBNAME: str = "tauth"
    TAUTH_MONGODB_URI: str = "mongodb://localhost:27017/"
    TAUTH_REDBABY_ALIAS: str = "tauth"

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    @classmethod
    @lru_cache(maxsize=1)
    def get(cls):
        return cls()
