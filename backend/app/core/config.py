from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "FRATELANZA REAL ESTATE PLATFORM"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://fratelanza:fratelanza_secret@localhost:5432/fratelanza_db"
    DATABASE_URL_SYNC: str = "postgresql://fratelanza:fratelanza_secret@localhost:5432/fratelanza_db"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "jwt-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_PATH: str = "./uploads"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"
    AWS_S3_ENDPOINT: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@fratelanza.com"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    SUPER_ADMIN_EMAIL: str = "admin@fratelanza.com"
    SUPER_ADMIN_PASSWORD: str = "Admin@123456"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
