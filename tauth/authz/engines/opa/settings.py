from pydantic_settings import BaseSettings, SettingsConfigDict


class OPASettings(BaseSettings):
    URL: str = "http://localhost"
    PORT: str = "8181"

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_prefix="TAUTH_AUTHZ_ENGINE_SETTINGS_OPA",
    )
