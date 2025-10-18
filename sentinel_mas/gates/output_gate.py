from __future__ import annotations
import json
from typing import Dict, Any, Optional

from sentinel_mas.policy_sentinel.audit_pg import write_audit
from .common import now_ms, sanitize_payload

def audit_gate_out(
    route: str,
    role: str,
    response: Dict[str, Any],
    *,
    request_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sanitize and log outgoing response BEFORE returning to caller.
    """
    safe_response = sanitize_payload(response)

    write_audit({
        "ts": now_ms(),
        "request_id": request_id,
        "route": route,
        "role": role,
        "tool_name": "gate_out",
        "decision": "ALLOW",
        "reason": "Egress",
        "args_json": json.dumps(safe_response, ensure_ascii=False),
        "error_type": None,
        "error_msg": None,
        "event_type": "GATE_OUT",
        "gate": "output",
        "user_id": user_id,
        "session_id": session_id,
    })
    return safe_response
