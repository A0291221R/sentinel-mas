# sentinel_mas/policy_sentinel/tool_guard.py
from __future__ import annotations

import os
import re
import json
import time
from typing import Any, Dict, Optional

from .audit_pg import write_audit
from .policy import (
    Role, Route,
    ROUTE_RBAC, TOOLS_ALLOWLIST,
    DISALLOWED_ATTR_KEYS, JAILBREAK_PATTERNS,
)

# ----------------------------
# Helpers
# ----------------------------
_SECRET_KEYS = {"api_key", "apikey", "token", "auth", "password", "secret", "authorization", "bearer", "key"}
_JAILBREAK_RE = re.compile("|".join(JAILBREAK_PATTERNS), flags=re.IGNORECASE)

def _now_ms() -> int:
    return int(time.time() * 1000)

def _gen_request_id() -> str:
    return f"req_{_now_ms()}_{os.getpid()}"

def _mask(value: Any) -> Any:
    if isinstance(value, str):
        return (value[:4] + "..." + value[-2:]) if len(value) > 8 else "***"
    if isinstance(value, (bytes, bytearray)):
        return f"<{type(value).__name__}:{len(value)} bytes>"
    return "***"

def _sanitize_args(args: Dict[str, Any], max_len: int = 10_000) -> Dict[str, Any]:
    """Sanitize secrets, large payloads, and remove disallowed attribute keys."""
    def scrub(k: str, v: Any) -> Any:
        lk = k.lower()
        if any(s in lk for s in _SECRET_KEYS):
            return _mask(v)
        if lk in DISALLOWED_ATTR_KEYS:
            return "<redacted-by-policy>"
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
        return {"_truncated": True, "preview": s[:max_len] + f"... (truncated {len(s)-max_len} chars)"}
    return safe

def _route_allowed_for_role(role: Role, route: Route) -> bool:
    return route in set(ROUTE_RBAC.get(role, []))

def _tool_allowed_for_route(route: Route, tool_name: str) -> bool:
    return tool_name in set(TOOLS_ALLOWLIST.get(route, []))

def _contains_jailbreak(payload: Dict[str, Any]) -> bool:
    for key in ("prompt", "message", "content", "query", "text", "instruction"):
        val = payload.get(key)
        if isinstance(val, str) and _JAILBREAK_RE.search(val):
            return True
    return False

# ----------------------------
# Guard API
# ----------------------------
def guard_tool_call(
    route: Route,
    role: Role,
    tool_name: str,
    args: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    gate: Optional[str] = None,  # usually None here; gates set this themselves
) -> Dict[str, Any]:
    """
    Enforce RBAC + tool allowlist + jailbreak/attr filters. ALWAYS audit.

    DENY when:
      - RBAC: role not allowed for route
      - Allowlist: tool not allowed for route
      - Jailbreak patterns detected in text inputs
    """
    rid = request_id or _gen_request_id()
    safe_args = _sanitize_args(args)

    # 1) RBAC
    if not _route_allowed_for_role(role, route):
        _audit_and_deny(
            rid, route, role, tool_name,
            reason=f"RBAC: role '{role}' not allowed for route '{route}'",
            user_id=user_id, session_id=session_id, gate=gate
        )

    # 2) Tool allowlist
    if not _tool_allowed_for_route(route, tool_name):
        _audit_and_deny(
            rid, route, role, tool_name,
            reason=f"TOOL_ALLOWLIST: tool '{tool_name}' not allowed for route '{route}'",
            user_id=user_id, session_id=session_id, gate=gate
        )

    # 3) Jailbreak checks
    if _contains_jailbreak(args):
        _audit_and_deny(
            rid, route, role, tool_name,
            reason="JAILBREAK_DETECTED",
            user_id=user_id, session_id=session_id, gate=gate
        )

    # 4) Allowed — record GUARD_ALLOW (pre-exec)
    write_audit({
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
        "event_type": "GUARD_ALLOW",
        "gate": gate,
        "user_id": user_id,
        "session_id": session_id,
    })

    # Return sanitized args to the tool
    return safe_args

def _audit_and_deny(
    request_id: str,
    route: Route,
    role: Role,
    tool_name: str,
    *,
    reason: str,
    user_id: Optional[str],
    session_id: Optional[str],
    gate: Optional[str],
) -> None:
    event = {
        "ts": _now_ms(),
        "request_id": request_id,
        "route": route,
        "role": role,
        "tool_name": tool_name,
        "decision": "DENY",
        "reason": reason,
        "args_json": json.dumps({"_redacted": True}),
        "error_type": "PermissionError",
        "error_msg": reason,
        "event_type": "GUARD_DENY",
        "gate": gate,
        "user_id": user_id,
        "session_id": session_id,
    }
    write_audit(event)
    raise PermissionError(reason)

def audit_tool_result(
    route: Route,
    role: Role,
    tool_name: str,
    args: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    write_audit({
        "ts": _now_ms(),
        "request_id": request_id or _gen_request_id(),
        "route": route,
        "role": role,
        "tool_name": tool_name,
        "decision": "ALLOW",
        "reason": "Executed",
        "args_json": json.dumps(_sanitize_args(args), ensure_ascii=False),
        "error_type": None,
        "error_msg": None,
        "event_type": "TOOL_EXECUTED",
        "gate": None,
        "user_id": user_id,
        "session_id": session_id,
    })

def audit_tool_error(
    route: Route,
    role: Role,
    tool_name: str,
    args: Dict[str, Any],
    exc: BaseException,
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    write_audit({
        "ts": _now_ms(),
        "request_id": request_id or _gen_request_id(),
        "route": route,
        "role": role,
        "tool_name": tool_name,
        "decision": "ERROR",
        "reason": "Exception during tool execution",
        "args_json": json.dumps(_sanitize_args(args), ensure_ascii=False),
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
        "event_type": "TOOL_ERROR",
        "gate": None,
        "user_id": user_id,
        "session_id": session_id,
    })
