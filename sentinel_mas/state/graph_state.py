from __future__ import annotations

from typing import Any, Dict, List, Literal, NotRequired, TypedDict

from langgraph.graph import MessagesState


class TraceEvent(TypedDict):
    ts: float
    node: str
    action: str
    detail: Dict[str, Any]
    reasoning_snippet: str


class ToolCallRecord(TypedDict):
    tool_name: str
    args: Dict[str, Any]
    result_summary: Dict[str, Any]
    duration_ms: int


class GraphState(MessagesState):
    user_question: str

    # pre-parsed time window (optional)
    start_ms: NotRequired[int]
    end_ms: NotRequired[int]
    time_label: NotRequired[str]

    # handy optional filters
    location_id: NotRequired[str]
    camera_id: NotRequired[str]

    # routing
    route: NotRequired[str]
    router_decision: NotRequired[Dict[str, Any]]

    # audit / identity metadata
    user_id: NotRequired[str]
    user_role: NotRequired[Literal["viewer", "operator", "supervisor", "admin"]]
    session_id: NotRequired[str]  # stable across a CLI/app session
    request_id: NotRequired[str]  # new per user turn

    # --- tool exec logs ---
    tool_calls: NotRequired[List[ToolCallRecord]]

    # --- timeline ---
    trace: NotRequired[List[TraceEvent]]

    # --- Audit logs ---
    audit_trail: NotRequired[List[Dict[str, Any]]]

    halt: NotRequired[bool]
