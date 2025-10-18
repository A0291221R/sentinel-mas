import os
from typing import Optional

import psycopg

DSN = os.getenv("SENTINEL_DSN", "postgresql://postgres:postgres@localhost:5432/sentinel")

AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id           BIGSERIAL PRIMARY KEY,
  ts_ms        BIGINT       NOT NULL,            -- event timestamp (ms)
  session_id   TEXT         NULL,                -- UI/session correlation id
  request_id   TEXT         NULL,                -- per-turn id (optional)
  user_id      TEXT         NOT NULL,
  role         TEXT         NOT NULL,
  route        TEXT         NULL,                -- SOP | EVENTS | TRACKING
  stage        TEXT         NOT NULL,            -- input | tool | output
  decision     TEXT         NOT NULL,            -- allow | block
  agent_name   TEXT         NULL,                -- e.g. events_agent
  tool_name    TEXT         NULL,                -- e.g. who_entered_zone
  latency_ms   INTEGER      NULL,                -- duration for this step
  rows         INTEGER      NULL,                -- number of rows returned (if any)
  detail       JSONB        NULL                 -- arbitrary structured info
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_audit_ts_ms      ON public.audit_logs (ts_ms);
CREATE INDEX IF NOT EXISTS idx_audit_route      ON public.audit_logs (route);
CREATE INDEX IF NOT EXISTS idx_audit_stage      ON public.audit_logs (stage);
CREATE INDEX IF NOT EXISTS idx_audit_user_role  ON public.audit_logs (user_id, role);
"""

def init_audit_schema(dsn: Optional[str] = None) -> None:
    with psycopg.connect(dsn or DSN, autocommit=True) as conn, conn.cursor() as cur:
        for stmt in AUDIT_TABLE_SQL.strip().split(";\n\n"):
            if stmt.strip():
                cur.execute(stmt + ";")


if __name__ == '__main__':
    init_audit_schema(DSN)
    print("✅ audit schema ensured")

