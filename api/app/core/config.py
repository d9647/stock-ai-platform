"""
API configuration.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Stock AI Platform API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"

    # API
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://stockai:stockai@192.168.5.126:5432/stockai_dev"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://192.168.5.126:6379/0")
    CACHE_TTL: int = 300  # 5 minutes default cache

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-jwt-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://192.168.5.126:3000").split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        case_sensitive = True


settings = Settings()
