from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    CENTRAL_URL = os.getenv("CENTRAL_URL", "http://localhost:8000")
    SENTINEL_DB_URL = os.getenv(
        "SENTINEL_DB_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/sentinel",
    )
    SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required config is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment")
        return True


Config.validate()

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_API = os.getenv("PUSHOVER_API")

# Langsmith for obeservability
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_WORKSPACE_ID = os.getenv("LANGSMITH_WORKSPACE_ID")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
