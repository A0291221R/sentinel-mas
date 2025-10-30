# sentinel_mas/policy_sentinel/tool_guard.py
from __future__ import annotations

import os
import json
import time
import traceback
from typing import Any, Dict, Optional, Callable

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ==============================
# AUDIT WRITER (independent engine; AUTOCOMMIT)
# ==============================
_AUDIT_DB_URL = os.getenv("AUDIT_DB_URL", os.getenv("DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sentinel"))

# Separate engine to prevent business-logic rollbacks from erasing audit rows.
_AUDIT_ENGINE = create_engine(
    _AUDIT_DB_URL,
    pool_pre_ping=True,
    future=True,
    isolation_level="AUTOCOMMIT",  # <-- critical
)
_AuditSession = sessionmaker(bind=_AUDIT_ENGINE, future=True)


def _write_audit_row(event: Dict[str, Any]) -> None:
    """
    Persist one audit record. Never raise back to caller.
    Schema expected: audit.tool_invocations
      (id BIGSERIAL PK,
       ts BIGINT,
       request_id TEXT,
       route TEXT,
       role TEXT,
       tool_name TEXT,
       decision TEXT,
       reason TEXT,
       args_json JSONB,
       error_type TEXT,
       error_msg TEXT)
    """
    try:
        with _AuditSession() as s:
            s.execute(
                text(
                    """
                    INSERT INTO audit.tool_invocations
                    (ts, request_id, route, role, tool_name, decision, reason, args_json, error_type, error_msg)
                    VALUES (:ts, :request_id, :route, :role, :tool_name, :decision, :reason, :args_json, :error_type, :error_msg)
                    """
                ),
                event,
            )
    except Exception:
        # Last-resort: don't break the app because audit failed.
        # Optionally log to stderr or a file, but avoid raising.
        pass


# ==============================
# POLICY HOOK (replace with your real policy)
# ==============================
# Example policy: routes -> allowed roles. Replace with your own source (DB/YAML/etc.)
_DEFAULT_POLICY = {
    # Example:
    # "TRACKING": {"admin", "system"},
    # "PAR": {"admin", "operator"},
    # "ANOMALY": {"admin"},
}


def is_role_allowed_for_route(role: str, route: str, policy: Optional[Dict[str, set]] = None) -> bool:
    p = policy or _DEFAULT_POLICY
    allowed = p.get(route)
    if allowed is None:
        # If a route isn't in policy, default-deny (safer)
        return False
    return role in allowed


# ==============================
# UTILITIES
# ==============================
_SECRET_KEYS = {"api_key", "apikey", "token", "auth", "password", "secret", "authorization", "bearer", "key"}


def _mask(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) <= 8:
            return "***"
        return value[:4] + "..." + value[-2:]
    if isinstance(value, (bytes, bytearray)):
        return f"<{type(value).__name__}:{len(value)} bytes>"
    return "***"


def _sanitize_args(args: Dict[str, Any], max_len: int = 10_000) -> Dict[str, Any]:
    """
    Remove/shorten sensitive or huge payloads to keep audit safe and compact.
    """
    def scrub(k: str, v: Any) -> Any:
        lk = k.lower()
        if any(s in lk for s in _SECRET_KEYS):
            return _mask(v)
        # Big blobs (images, binary, long strings/lists) → summarize
        if isinstance(v, (bytes, bytearray)):
            return f"<{type(v).__name__}:{len(v)} bytes>"
        if isinstance(v, str) and len(v) > 512:
            return v[:512] + f"... (truncated {len(v)-512} chars)"
        if isinstance(v, (list, tuple)) and len(v) > 64:
            return list(v[:64]) + [f"... (+{len(v)-64} more)"]
        if isinstance(v, dict):
            return {ik: scrub(ik, iv) for ik, iv in v.items()}
        return v

    safe = {k: scrub(k, v) for k, v in (args or {}).items()}

    s = json.dumps(safe, ensure_ascii=False)
    if len(s) > max_len:
        # final hard cap
        return {"_truncated": True, "preview": s[:max_len] + f"... (truncated {len(s)-max_len} chars)"}
    return safe


def _now_ms() -> int:
    return int(time.time() * 1000)


def _gen_request_id() -> str:
    # Simple, collision-resistant enough for audit correlation
    return f"req_{_now_ms()}_{os.getpid()}"


# ==============================
# PUBLIC GUARD API
# ==============================
def guard_tool_call(
    route: str,
    role: str,
    tool_name: str,
    args: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    policy: Optional[Dict[str, set]] = None,
) -> Dict[str, Any]:
    """
    Enforce route/role policy and ALWAYS audit the decision.
    On DENY: writes a 'DENY' record, then raises PermissionError.
    On ALLOW: returns sanitized args (so caller uses safe args).
    """
    rid = request_id or _gen_request_id()
    sanitize = arg_sanitizer or _sanitize_args
    safe_args = sanitize(args)

    allowed = is_role_allowed_for_route(role, route, policy=policy)
    writer = audit_writer or _write_audit_row

    if not allowed:
        event = {
            "ts": _now_ms(),
            "request_id": rid,
            "route": route,
            "role": role,
            "tool_name": tool_name,
            "decision": "DENY",
            "reason": f"Role '{role}' not allowed for route '{route}'",
            "args_json": json.dumps(safe_args, ensure_ascii=False),
            "error_type": "PermissionError",
            "error_msg": f"Role '{role}' not allowed for route '{route}'",
        }
        try:
            writer(event)
        finally:
            # Raise AFTER persisting audit
            raise PermissionError(event["error_msg"])

    # Allowed path → pre-log ALLOW (decision=ALLOW, reason=GuardPassed)
    pre_event = {
        "ts": _now_ms(),
        "request_id": rid,
        "route": route,
        "role": role,
        "tool_name": tool_name,
        "decision": "ALLOW",
        "reason": "GuardPassed",
        "args_json": json.dumps(safe_args, ensure_ascii=False),
        "error_type": None,
        "error_msg": None,
    }
    try:
        writer(pre_event)
    except Exception:
        # Don't block execution if audit pre-log fails
        pass

    return safe_args


def audit_tool_result(
    route: str,
    role: str,
    tool_name: str,
    args: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    status: str = "Executed",
) -> None:
    """
    Optional helper to log a post-execution ALLOW record (e.g., from the router).
    """
    writer = _write_audit_row
    safe_args = _sanitize_args(args)
    event = {
        "ts": _now_ms(),
        "request_id": request_id or _gen_request_id(),
        "route": route,
        "role": role,
        "tool_name": tool_name,
        "decision": "ALLOW",
        "reason": status,
        "args_json": json.dumps(safe_args, ensure_ascii=False),
        "error_type": None,
        "error_msg": None,
    }
    try:
        writer(event)
    except Exception:
        pass


def audit_tool_error(
    route: str,
    role: str,
    tool_name: str,
    args: Dict[str, Any],
    exc: BaseException,
    *,
    request_id: Optional[str] = None,
    reason: str = "Exception during tool execution",
) -> None:
    """
    Optional helper to log unexpected errors from the router/orchestrator.
    """
    writer = _write_audit_row
    safe_args = _sanitize_args(args)
    event = {
        "ts": _now_ms(),
        "request_id": request_id or _gen_request_id(),
        "route": route,
        "role": role,
        "tool_name": tool_name,
        "decision": "ERROR",
        "reason": reason,
        "args_json": json.dumps(safe_args, ensure_ascii=False),
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
    }
    try:
        writer(event)
    except Exception:
        pass


# ==============================
# (OPTIONAL) QUICK SELF-TEST
# Run: uv run python -m sentinel_mas.policy_sentinel.tool_guard
# ==============================
if __name__ == "__main__":
    # Example: define a basic policy at runtime
    _DEFAULT_POLICY.update({
        "TRACKING": {"admin", "system"},
        "PAR": {"admin", "operator"},
    })

    # Expect DENY → audit row with decision=DENY, then PermissionError
    try:
        guard_tool_call("TRACKING", "operator", "start_tracking", {"target_id": 123}, request_id="demo-deny-1")
    except PermissionError as e:
        print("DENY path OK:", e)

    # Expect ALLOW pre-log
    safe = guard_tool_call("PAR", "operator", "par_infer", {"image": "base64:..."}, request_id="demo-allow-1")
    print("ALLOW path OK, sanitized args:", safe.keys())
    # Simulate successful execution log
    audit_tool_result("PAR", "operator", "par_infer", {"image": "base64:..."}, request_id="demo-allow-1", status="Executed")
    # Simulate error log
    try:
        raise RuntimeError("simulated failure")
    except Exception as ex:
        audit_tool_error("PAR", "operator", "par_infer", {"image": "base64:..."}, ex, request_id="demo-allow-1")
