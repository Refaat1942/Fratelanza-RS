from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FRATELANZA REAL ESTATE PLATFORM"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-this-secret-key", min_length=16)
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite+pysqlite:///./fratelanza.db"
    redis_url: str = "redis://localhost:6379/0"
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    storage_provider: str = "local"
    local_storage_path: str = "./storage"
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
