# sentinel_mas/policy_sentinel/audit.py
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

# runtime must expose:
#   get_context() -> SentinelContext (immutable per-request identity)
#   get_graph_state() -> Dict[str, Any] (mutable working memory for this request)
from sentinel_mas.policy_sentinel import runtime
from sentinel_mas.policy_sentinel.policy import redactor

# ---------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------

DecisionType = Literal["ALLOW", "DENY", "ERROR"]
PhaseType = Literal[
    "pre", "exec", "post"
]  # "pre" = guard stage, "post" = after tool call


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _now_iso() -> str:
    """
    UTC ISO8601 with milliseconds and 'Z' suffix.
    Example: '2025-10-27T14:22:11.123Z'
    """
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _gen_request_id() -> str:
    """
    Fallback request_id if not provided in context.
    """
    return "req_" + uuid.uuid4().hex[:8]


def write_audit(event: Dict[str, Any]) -> None:
    """
    Simple dev-mode audit sink: prints structured JSON to stdout.

    In production you could replace this with:
    - a DB insert (PostgreSQL / Elasticsearch / Loki)
    - an HTTP log collector
    - or a structured file logger.

    For local testing, this prints color-coded JSON to console.
    """
    try:
        # add timestamp if missing
        event.setdefault(
            "ts", datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        )

        # pretty-print compact JSON line
        json_line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        print(f"[AUDIT] {json_line}", file=sys.stdout, flush=True)

    except Exception as e:
        # Never crash the app because of audit failure
        print(
            f"[AUDIT_ERROR] Failed to log audit event: {e}", file=sys.stderr, flush=True
        )


# ---------------------------------------------------------------------
# Canonical audit event schema
# ---------------------------------------------------------------------


@dataclass
class AuditEvent:
    # identity / timestamp
    event_id: str
    ts_iso: str

    # caller / session / routing context
    request_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    route: Optional[str]
    role: Optional[str]

    # tool call info
    tool: str
    tool_args: Dict[str, Any] | str

    # lifecycle
    phase: PhaseType  # "pre" | "exec" | "post"
    decision: DecisionType  # "ALLOW" | "DENY" | "ERROR"
    detail: Optional[str]  # explanation / reason / notes

    # result diagnostic
    result_status: Optional[str]  # "OK", "ERROR", etc.
    result_error: Optional[str]  # error string
    result_payload_preview: Optional[Any]  # SAFE + SMALL preview of tool result

    # classification
    event_type: str  # "GUARD_DENY" | "TOOL_EXECUTED" | "TOOL_ERROR"

    # untrusted but useful for forensics
    user_question_snapshot: Optional[str] = None


def _extract_context() -> Dict[str, Any]:
    """
    Collects:
    - Stable identity from runtime.get_context() (trusted, immutable for this request)
    - Mutable graph state from runtime.get_graph_state() (working memory)
    - user_question from state (untrusted, but useful to log)
    """
    ctx_obj = runtime.get_context()  # SentinelContext dataclass (frozen)
    state = runtime.get_graph_state()  # GraphState dict (mutable)

    # identity (trusted)
    request_id = ctx_obj.request_id or _gen_request_id()
    user_id = ctx_obj.user_id or "unknown"
    role = ctx_obj.user_role or "operator"
    route = ctx_obj.route
    session_id = ctx_obj.session_id

    # route fallback: maybe router only wrote to graph state
    if route is None:
        route = (
            state.get("route")
            or (state.get("router_decision") or {}).get("route")
            or None
        )

    # user_question is untrusted text but still valuable for evidence/tracing
    user_question_snapshot = state.get("user_question")

    return {
        "state": state,
        "request_id": request_id,
        "user_id": user_id,
        "session_id": session_id,
        "route": route,
        "role": role,
        "user_question_snapshot": user_question_snapshot,
    }


def build_audit_event(
    *,
    phase: PhaseType,
    decision: DecisionType,
    event_type: str,
    tool: str,
    tool_args: Dict[str, Any],
    detail: Optional[str] = None,
    result_status: Optional[str] = None,
    result_error: Optional[str] = None,
    result_payload_preview: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build a normalized audit record dict (JSON-safe).
    - Security-critical identity comes from get_context()
    - Execution trace info (like user_question) comes from graph state
    """
    ctx = _extract_context()

    evt = AuditEvent(
        event_id=str(uuid.uuid4()),
        ts_iso=_now_iso(),
        request_id=ctx["request_id"],
        user_id=ctx["user_id"],
        session_id=ctx["session_id"],
        route=ctx["route"],
        role=ctx["role"],
        tool=tool,
        tool_args=redactor.redact_args(tool_args),
        phase=phase,
        decision=decision,
        detail=detail,
        result_status=result_status,
        result_error=result_error,
        result_payload_preview=result_payload_preview,
        event_type=event_type,
        user_question_snapshot=ctx["user_question_snapshot"],
    )

    return asdict(evt)


def _append_to_graph_state_trail(
    state: Dict[str, Any],
    audit_event: Dict[str, Any],
) -> None:
    """
    Append to in-flight GraphState.
    Safe even if audit_trail doesn't exist yet.
    """
    state.setdefault("audit_trail", [])
    state["audit_trail"].append(audit_event)


def record_audit(audit_event: Dict[str, Any]) -> None:
    """
    Central sink:
    1. append into the active graph state's audit_trail (for UI/debug/return)
    2. forward to persistent sink write_audit() (for forensic log / SIEM)
    """
    ctx = _extract_context()
    state = ctx["state"]

    _append_to_graph_state_trail(state, audit_event)
    write_audit(audit_event)


def guard_deny_and_raise(
    *,
    tool_name: str,
    reason: str,
    gate: Optional[str] = None,
) -> None:
    """
    Called by any guard layer (RBAC, prompt-injection check, policy gate)
    BEFORE executing a tool.

    Logs a DENY event and raises PermissionError.
    """
    audit_event = build_audit_event(
        phase="pre",
        decision="DENY",
        event_type="GUARD_DENY",
        tool=tool_name,
        tool_args={
            "_redacted": True,
            "gate": gate,
        },
        detail=reason,
        result_status=None,
        result_error=reason,
        result_payload_preview=None,
    )

    record_audit(audit_event)
    raise PermissionError(reason)


def audit_guard_allow(
    *,
    tool_name: str,
    detail: str = "All guard checks passed",
) -> None:
    """
    Record a 'GUARD_ALLOW' event before executing a tool.

    This is logged when the tool passes all policy/injection/rbac checks.
    """
    audit_event = build_audit_event(
        phase="pre",
        decision="ALLOW",
        event_type="GUARD_ALLOW",
        tool=tool_name,
        tool_args={"_redacted": True},  # we don’t store real args yet
        detail=detail,
        result_status=None,
        result_error=None,
        result_payload_preview=None,
    )

    record_audit(audit_event)


def audit_tool_success(
    *,
    tool_name: str,
    raw_args: Dict[str, Any],
    result_preview: Any,
) -> None:
    """
    Call AFTER a tool finishes successfully.

    result_preview MUST be a safe, lightweight summary:
    e.g. {"ok": True, "status_code": 200} or {"count": 3}
    """
    audit_event = build_audit_event(
        phase="post",
        decision="ALLOW",
        event_type="TOOL_EXECUTED",
        tool=tool_name,
        tool_args=raw_args,
        detail="Executed",
        result_status="OK",
        result_error=None,
        result_payload_preview=result_preview,
    )

    record_audit(audit_event)


def audit_tool_failure(
    *,
    tool_name: str,
    raw_args: Dict[str, Any],
    exc: BaseException,
) -> None:
    """
    Call AFTER a tool raised an exception.
    We log it as ERROR and let the caller decide whether to re-raise.
    """
    audit_event = build_audit_event(
        phase="post",
        decision="ERROR",
        event_type="TOOL_ERROR",
        tool=tool_name,
        tool_args=raw_args,
        detail="Exception during tool execution",
        result_status="ERROR",
        result_error=f"{type(exc).__name__}: {exc}",
        result_payload_preview=None,
    )

    record_audit(audit_event)
    # Do NOT raise here. Caller (secure executor) can choose to raise.
