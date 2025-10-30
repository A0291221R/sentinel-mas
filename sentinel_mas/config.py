from __future__ import annotations
from dotenv import load_dotenv

import os

load_dotenv(override=True)


SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
SENTINEL_DB_URL = os.getenv("SENTINEL_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sentinel")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_API = os.getenv("PUSHOVER_API")

# Langsmith for obeservability
LANGSMITH_TRACING = os.getenv('LANGSMITH_TRACING')
LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY')
LANGSMITH_WORKSPACE_ID = os.getenv('LANGSMITH_WORKSPACE_ID')
LANGCHAIN_PROJECT = os.getenv('LANGCHAIN_PROJECT')
