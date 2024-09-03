from pydantic_settings import BaseSettings, SettingsConfigDict


class RemoteSettings(BaseSettings):
    API_URL: str

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_prefix="TAUTH_AUTHZ_ENGINE_SETTINGS_REMOTE_",
    )
