-- === Canonical audit table (governance-grade) ===============================
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.tool_invocations (
  id           BIGSERIAL PRIMARY KEY,
  ts           BIGINT       NOT NULL,            -- epoch ms
  request_id   TEXT,
  route        TEXT         NOT NULL,
  role         TEXT         NOT NULL,
  tool_name    TEXT         NOT NULL,
  decision     TEXT         NOT NULL,            -- ALLOW | DENY | ERROR
  reason       TEXT,                             
  args_json    JSONB,
  error_type   TEXT,
  error_msg    TEXT
);

-- === Add "missing" columns (safe even if they already exist) ================
ALTER TABLE audit.tool_invocations
  ADD COLUMN IF NOT EXISTS event_type TEXT DEFAULT 'TOOL_EXECUTED',
  ADD COLUMN IF NOT EXISTS gate       TEXT,       -- 'input' | 'output' | NULL
  ADD COLUMN IF NOT EXISTS user_id    TEXT,
  ADD COLUMN IF NOT EXISTS session_id TEXT;

-- === Constraints (add only if not already present) ==========================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'tool_inv_decision_ck'
  ) THEN
    ALTER TABLE audit.tool_invocations
      ADD CONSTRAINT tool_inv_decision_ck
      CHECK (decision IN ('ALLOW','DENY','ERROR'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'tool_inv_event_type_ck'
  ) THEN
    ALTER TABLE audit.tool_invocations
      ADD CONSTRAINT tool_inv_event_type_ck
      CHECK (event_type IN ('GATE_IN','GATE_OUT','GUARD_ALLOW','GUARD_DENY','TOOL_EXECUTED','TOOL_ERROR','OTHER'));
  END IF;
END$$;

-- === Indexes (hot paths) ====================================================
CREATE INDEX IF NOT EXISTS idx_toolinv_ts             ON audit.tool_invocations (ts);
CREATE INDEX IF NOT EXISTS idx_toolinv_request_id     ON audit.tool_invocations (request_id);
CREATE INDEX IF NOT EXISTS idx_toolinv_route_role     ON audit.tool_invocations (route, role);
CREATE INDEX IF NOT EXISTS idx_toolinv_tool           ON audit.tool_invocations (tool_name);
CREATE INDEX IF NOT EXISTS idx_toolinv_reason         ON audit.tool_invocations (reason);
CREATE INDEX IF NOT EXISTS idx_toolinv_decision_ts    ON audit.tool_invocations (decision, ts DESC);
CREATE INDEX IF NOT EXISTS idx_toolinv_eventtype_ts   ON audit.tool_invocations (event_type, ts DESC);
CREATE INDEX IF NOT EXISTS idx_toolinv_deny_recent
  ON audit.tool_invocations (ts DESC) WHERE decision = 'DENY';

-- === Back-compat view (optional) ============================================
-- If you previously queried audit.audit_logs, expose a view that maps to the new table.
CREATE OR REPLACE VIEW audit.audit_logs AS
SELECT
  id, ts, request_id, route, role, tool_name, decision, reason,
  args_json, error_type, error_msg, gate, user_id, session_id
FROM audit.tool_invocations
WHERE event_type IN ('GATE_IN','GATE_OUT','OTHER');
