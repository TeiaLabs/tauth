from pydantic_settings import BaseSettings, SettingsConfigDict


class OPASettings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 8181

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_prefix="TAUTH_AUTHZ_ENGINE_SETTINGS_OPA_",
    )
