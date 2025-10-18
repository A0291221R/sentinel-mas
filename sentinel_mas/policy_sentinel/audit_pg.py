# sentinel_mas/policy_sentinel/audit_pg.py
from __future__ import annotations

import os
from typing import Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Separate AUTOCOMMIT engine so audit rows survive business rollbacks.
_AUDIT_DB_URL = os.getenv("AUDIT_DB_URL", os.getenv("DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sentinel"))
_ENGINE = create_engine(
    _AUDIT_DB_URL,
    pool_pre_ping=True,
    future=True,
    isolation_level="AUTOCOMMIT",
)
_Session = sessionmaker(bind=_ENGINE, future=True)

_SQL = text("""
INSERT INTO audit.tool_invocations
(ts, request_id, route, role, tool_name, decision, reason, args_json,
 error_type, error_msg, event_type, gate, user_id, session_id)
VALUES (:ts, :request_id, :route, :role, :tool_name, :decision, :reason, :args_json,
        :error_type, :error_msg, :event_type, :gate, :user_id, :session_id)
""")

def write_audit(event: Dict[str, Any]) -> None:
    """Fire-and-forget audit insert. Never raises upstream."""
    try:
        with _Session() as s:
            s.execute(_SQL, event)
    except Exception:
        # Intentionally swallow errors to never break main path.
        pass
