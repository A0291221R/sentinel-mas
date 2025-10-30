from __future__ import annotations
from dataclasses import dataclass
from typing import TypedDict, List, Literal, Optional, Dict, Any, NotRequired
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
    user_role: NotRequired[Literal["viewer","operator","supervisor","admin"]]
    session_id: NotRequired[str]     # stable across a CLI/app session
    request_id: NotRequired[str]     # new per user turn

    # --- tool exec logs ---
    tool_calls: List[ToolCallRecord]

    # --- timeline ---
    trace: List[TraceEvent]

    # --- Audit logs ---
    audit_trail: List[Dict[str, Any]]

    halt: NotRequired[bool]

# class GraphState(TypedDict, total=False):
#     # --- identity / audit ---
#     trace_id: str
#     request_id: str
#     session_id: str
#     user_id: str
#     user_role: str
#     timestamp_utc: str

#     # --- user question & history ---
#     user_input: str
#     history: List[Dict[str, str]]

#     # --- routing ---
#     route: Literal["TRACKING","EVENTS","SOP"]
#     route_confidence: float
#     route_reasoning: str
#     agent_name: str

#     # --- tool exec logs ---
#     tool_calls: List[ToolCallRecord]

#     # --- final answer ---
#     agent_output: str
#     status: Literal["OK","FAILED"]
#     error_msg: Optional[str]

#     # --- timeline ---
#     trace: List[TraceEvent]

#     # --- perf ---
#     started_at_ms: float
#     ended_at_ms: float
#     latency_ms: int
