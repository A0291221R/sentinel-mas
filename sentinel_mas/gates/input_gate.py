from __future__ import annotations
import json
from typing import Dict, Any, Optional

from sentinel_mas.policy_sentinel.audit_pg import write_audit
from .common import now_ms, sanitize_payload, contains_jailbreak

def audit_gate_in(
    route: str,
    role: str,
    payload: Dict[str, Any],
    *,
    request_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate & log incoming request BEFORE any guard/tool is invoked.
    Returns sanitized payload if allowed.
    Raises PermissionError on jailbreak or policy violation.
    """
    safe_payload = sanitize_payload(payload)

    if contains_jailbreak(payload):
        reason = "JAILBREAK_DETECTED"
        write_audit({
            "ts": now_ms(),
            "request_id": request_id,
            "route": route,
            "role": role,
            "tool_name": "gate_in",
            "decision": "DENY",
            "reason": reason,
            "args_json": json.dumps({"_redacted": True}),
            "error_type": "PermissionError",
            "error_msg": reason,
            "event_type": "GATE_IN",
            "gate": "input",
            "user_id": user_id,
            "session_id": session_id,
        })
        raise PermissionError(reason)

    # Allowed ingress
    write_audit({
        "ts": now_ms(),
        "request_id": request_id,
        "route": route,
        "role": role,
        "tool_name": "gate_in",
        "decision": "ALLOW",
        "reason": "Ingress",
        "args_json": json.dumps(safe_payload, ensure_ascii=False),
        "error_type": None,
        "error_msg": None,
        "event_type": "GATE_IN",
        "gate": "input",
        "user_id": user_id,
        "session_id": session_id,
    })
    return safe_payload
