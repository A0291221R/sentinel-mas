# scripts/create_audit_schema.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

DDL = r"""
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.tool_invocations (
  id           BIGSERIAL PRIMARY KEY,
  ts           BIGINT NOT NULL,
  request_id   TEXT,
  route        TEXT NOT NULL,
  role         TEXT NOT NULL,
  tool_name    TEXT NOT NULL,
  decision     TEXT NOT NULL,
  reason       TEXT,
  args_json    JSONB,
  error_type   TEXT,
  error_msg    TEXT
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'tool_invocations_decision_ck'
  ) THEN
    ALTER TABLE audit.tool_invocations
      ADD CONSTRAINT tool_invocations_decision_ck
      CHECK (decision IN ('ALLOW','DENY','ERROR'));
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_toolinv_ts           ON audit.tool_invocations (ts);
CREATE INDEX IF NOT EXISTS idx_toolinv_decision_ts  ON audit.tool_invocations (decision, ts DESC);
CREATE INDEX IF NOT EXISTS idx_toolinv_request_id   ON audit.tool_invocations (request_id);
CREATE INDEX IF NOT EXISTS idx_toolinv_route_role   ON audit.tool_invocations (route, role);
CREATE INDEX IF NOT EXISTS idx_toolinv_tool         ON audit.tool_invocations (tool_name);

CREATE INDEX IF NOT EXISTS idx_toolinv_deny_recent
  ON audit.tool_invocations (ts DESC)
  WHERE decision = 'DENY';
"""

def main() -> int:
    db_url = os.getenv("AUDIT_DB_URL") or os.getenv("DB_URL")
    if not db_url:
        print("ERROR: Set AUDIT_DB_URL or DB_URL (e.g. postgresql+psycopg://user:pass@host:5432/dbname)")
        return 2

    # Separate autocommit engine ensures DDL succeeds even if caller wraps in transactions
    engine = create_engine(db_url, future=True, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
    with engine.begin() as conn:
        for stmt in [s.strip() for s in DDL.split(";\n\n") if s.strip()]:
            conn.execute(text(stmt))
    print("✅ audit.tool_invocations schema ensured.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
