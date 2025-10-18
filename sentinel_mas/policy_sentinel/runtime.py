# sentinel_mas/policy_sentinel/runtime.py
from __future__ import annotations
import contextvars
from typing import Optional

_user_id     = contextvars.ContextVar("user_id", default="unknown")
_user_role   = contextvars.ContextVar("user_role", default="operator")
_route       = contextvars.ContextVar("route", default=None)   # "SOP" | "EVENTS" | "TRACKING" | None
_request_id  = contextvars.ContextVar("request_id", default=None)
_session_id  = contextvars.ContextVar("session_id", default=None)

def set_context_from_state(state: dict) -> None:
    if "user_id" in state:    _user_id.set(state["user_id"])
    if "user_role" in state:  _user_role.set(state["user_role"])
    if "route" in state:      _route.set(state["route"])
    elif "router_decision" in state and state["router_decision"]:
        _route.set(state["router_decision"].get("route"))
    if "request_id" in state: _request_id.set(state["request_id"])
    if "session_id" in state: _session_id.set(state["session_id"])

def get_context() -> dict:
    return {
        "user_id": _user_id.get(),
        "user_role": _user_role.get(),
        "route": _route.get(),
        "request_id": _request_id.get(),
        "session_id": _session_id.get(),
    }
