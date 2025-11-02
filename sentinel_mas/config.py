"""
Sentinel MAS Package Configuration

Reads from .env.sentinel and .env.shared files.
Clean variable names, no prefixes!
"""

from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(".env.sentinel")


class SentinelMASConfig(BaseSettings):
    """Configuration for Sentinel MAS package"""

    # Core Settings
    SENTINEL_CENTRAL_URL: str = "http://localhost:8000"
    SENTINEL_DB_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/sentinel"
    )
    SENTINEL_API_KEY: Optional[str] = None

    # OpenAI Settings
    OPENAI_API_KEY: str = "sk-xxx"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Pushover Settings
    PUSHOVER_TOKEN: Optional[str] = None
    PUSHOVER_USER: Optional[str] = None
    PUSHOVER_API: Optional[str] = None

    # LangSmith Settings
    LANGSMITH_TRACING: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None

    # Agent Settings
    RECURSION_LIMIT: int = 15
    MAX_ITERATIONS: int = 10
    TIMEOUT: int = 300

    # Shared Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    def validate_required(self) -> bool:
        """Validate required config"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in .env.sentinel")
        return True

    class Config:
        env_file = [".env.sentinel", ".env.shared"]
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_config() -> SentinelMASConfig:
    """Get cached config instance"""
    config = SentinelMASConfig()
    config.validate_required()
    return config


# Backwards Compatibility
_config = get_config()


class Config:
    """Backward compatible Config class"""

    SENTINEL_CENTRAL_URL = _config.SENTINEL_CENTRAL_URL
    SENTINEL_DB_URL = _config.SENTINEL_DB_URL
    SENTINEL_API_KEY = _config.SENTINEL_API_KEY
    OPENAI_API_KEY = _config.OPENAI_API_KEY
    OPENAI_MODEL = _config.OPENAI_MODEL

    @classmethod
    def validate(cls) -> bool:
        return _config.validate_required()


Config.validate()
