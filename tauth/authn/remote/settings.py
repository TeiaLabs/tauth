from pydantic_settings import BaseSettings, SettingsConfigDict


class RemoteSettings(BaseSettings):
    API_URL: str = "http://localhost:8080"

    model_config = SettingsConfigDict(
        env_prefix="TAUTH_AUTHN_ENGINE_SETTINGS_REMOTE_",
        extra="ignore",
        env_file=".env",
    )
