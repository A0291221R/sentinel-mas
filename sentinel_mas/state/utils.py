import time
from typing import Dict, Any
from .graph_state import GraphState, TraceEvent, ToolCallRecord

def now_ms() -> float:
    return time.time() * 1000.0

def _audit_context_from_state(state: GraphState) -> Dict[str, Any]:
    """
    Common metadata we want on EVERY trace event for accountability / forensics.
    """
    return {
        "request_id": state.get("request_id"),
        "session_id": state.get("session_id"),
        "user_id": state.get("user_id"),
        "user_role": state.get("user_role"),
        "user_question": state.get("user_input"),
    }

def append_trace(
    state: GraphState,
    *,
    node: str,
    action: str,
    detail: Dict[str, Any],
    reasoning_snippet: str,
) -> None:
    """
    Append a trace event with:
      - node: which logical component ran (router, tracking_agent, finalize, etc.)
      - action: what step happened (ROUTE_DECISION, TOOL_CALL, FINAL_REPLY, END)
      - detail: step-specific info (route_info, tool_exec, etc.)
      - reasoning_snippet: short human-facing justification

    Automatically injects core audit context:
      request_id, session_id, user_id, user_role, user_question
    """
    evt: TraceEvent = {
        "ts": time.time(),
        "node": node,
        "action": action,
        "detail": {
            # keep your node-specific structured data
            **detail,
            # plus a standard audit block
            "audit": _audit_context_from_state(state),
        },
        "reasoning_snippet": reasoning_snippet[:300],
    }
    state.setdefault("trace", [])
    state["trace"].append(evt)

def record_tool_call(
    state: GraphState,
    *,
    tool_name: str,
    args: Dict[str, Any],
    result_summary: Dict[str, Any],
    duration_ms: int,
) -> None:
    """
    Lightweight per-tool record for dashboards/metrics, not as verbose as trace.
    We don't need to inline audit again here because trace already has it.
    """
    rec: ToolCallRecord = {
        "tool_name": tool_name,
        "args": args,
        "result_summary": result_summary,
        "duration_ms": duration_ms,
    }
    state.setdefault("tool_calls", [])
    state["tool_calls"].append(rec)
