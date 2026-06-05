# notes-fastapi/app/core/config.py
from datetime import timedelta
from pathlib import Path
from typing import Any

from pydantic.v1 import BaseSettings, validator, EmailStr
from sqlalchemy import URL


class Settings(BaseSettings):
    # Main
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_NAME: str = "notes-fastapi"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    API_BASE_URL: str  # required
    FRONTEND_BASE_URL: str  # required

    # Timezone Configuration
    TIMEZONE: str = "Asia/Yerevan"

    # Security
    SECRET_KEY: str  # required
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_LIFETIME: timedelta = timedelta(minutes=30)
    REFRESH_TOKEN_LIFETIME: timedelta = timedelta(days=30)
    REFRESH_TOKEN_BLACKLIST: bool = True

    # Database Components
    DB_HOST: str  # required
    DB_PORT: int  # required
    DB_USER: str  # required
    DB_PASSWORD: str  # required
    DB_NAME: str  # required
    DATABASE_URL: str | None = None  # optional

    @validator("DATABASE_URL", pre=True)
    def set_db_connection_string(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str) and v.strip():
            return v
        return URL.create(
            drivername="postgresql",
            username=values.get("DB_USER"),
            password=values.get("DB_PASSWORD"),
            host=values.get("DB_HOST"),
            port=values.get("DB_PORT"),
            database=values.get("DB_NAME"),
        ).render_as_string(hide_password=False)

    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = []  # optional

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def set_cors_origins(cls, v: str | list[str] | None, values: dict[str, Any]) -> list[str]:
        # Start with the defaults already defined on the class or fall back
        default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

        if not v:
            return default_origins

        if isinstance(v, str):
            extra_origins = [i.strip() for i in v.split(",") if i.strip()]
            return list(set(default_origins + extra_origins))

        if isinstance(v, list):
            return list(set(default_origins + v))

        return default_origins

    # email configs
    EMAIL_FROM: EmailStr  # required
    EMAIL_PASSWORD: str  # required
    EMAIL_PORT: int = 587
    EMAIL_SERVER: str = "smtp.gmail.com"
    EMAIL_TLS: bool = True
    EMAIL_SSL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
