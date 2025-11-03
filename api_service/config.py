"""
API Service Configuration

Reads from .env.api and .env.shared files.
"""

from functools import lru_cache
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings

from sentinel_mas.config import SentinelMASConfig


class APIConfig(BaseSettings):
    """
    API Service configuration

    This class defines all configuration needed for the API service.
    Values are loaded from .env.api and .env.shared files.
    """

    # ============================================
    # JWT Settings
    # ============================================
    SECRET_KEY: str = "secret-xxx"  # Used to sign JWT tokens
    ALGORITHM: str = "HS256"  # JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Token expiration time

    # ============================================
    # Server Settings
    # ============================================
    HOST: str = "0.0.0.0"  # nosec B104 - Required for Docker/container environments
    PORT: int = 8000  # API server port
    V1_PREFIX: str = "/api/v1"  # API version prefix

    # ============================================
    # Application Info
    # ============================================
    PROJECT_NAME: str = "Sentinel MAS API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False  # Debug mode (more logging)

    # ============================================
    # CORS (Cross-Origin Resource Sharing)
    # ============================================
    # List of origins that can access this API
    ALLOWED_ORIGINS: List[str] | str = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # API server itself
    ]

    # ============================================
    # Rate Limiting (optional)
    # ============================================
    RATE_LIMIT_PER_MINUTE: int = 60  # Max requests per minute

    # ============================================
    # Shared Settings (from .env.shared)
    # ============================================
    ENVIRONMENT: str = "development"  # dev, staging, production
    LOG_LEVEL: str = "INFO"  # Logging level

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls: Any, v: Any) -> Any:
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            # If it's a comma-separated string, split it
            return [origin.strip() for origin in v.split(",")]
        return v

    def validate_required(self) -> bool:
        """
        Validate that required configuration is present

        Raises ValueError if SECRET_KEY is not properly set
        """
        DEFAULT_SECRET = "change-me"  # nosec B105 - Used only for validation
        if not self.SECRET_KEY or self.SECRET_KEY == DEFAULT_SECRET:
            raise ValueError(
                "SECRET_KEY must be set in .env.api\n"
                "Generate one with: openssl rand -hex 32"
            )
        return True

    class Config:
        # Load from both .env.api and .env.shared
        # Later files override earlier ones
        env_file = [".env.api", ".env.shared"]
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra variables


@lru_cache()
def get_api_config() -> APIConfig:
    """
    Get cached API config instance

    Uses lru_cache to only load config once.
    Validates on first load.

    Returns:
        APIConfig: Validated configuration object
    """
    config = APIConfig()
    config.validate_required()
    return config


def get_sentinel_config() -> SentinelMASConfig:
    """
    Get sentinel_mas configuration from API service

    This allows API service to access sentinel settings if needed.
    For example, to show which model is being used.
    """
    from sentinel_mas.config import get_config

    return get_config()
