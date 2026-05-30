from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CampusHub IA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Base de données (SQLite pour le développement)
    DATABASE_URL: str = "sqlite+aiosqlite:///./campushub.db"

    # Sécurité JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Email (optionnel)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    EMAIL_FROM: str = "noreply@campushub.app"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()