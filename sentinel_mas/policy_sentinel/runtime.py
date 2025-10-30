# sentinel_mas/policy_sentinel/runtime.py
from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Dict, Any


# ===============================================================
# 1. SentinelContext — Immutable per-request identity envelope
# ===============================================================

@dataclass(frozen=True)
class SentinelContext:
    user_id: str = "unknown"          # who is acting
    user_role: str = "operator"       # RBAC role (operator/admin/etc.)
    route: Optional[str] = None       # SOP / EVENTS / TRACKING / etc.
    request_id: Optional[str] = None  # trace id for request
    session_id: Optional[str] = None  # conversational session id


# The single ContextVar holding the current context
_context_var: contextvars.ContextVar[SentinelContext] = contextvars.ContextVar(
    "sentinel_context",
    default=SentinelContext(),
)


def get_context() -> SentinelContext:
    """Return the current request-scoped SentinelContext."""
    return _context_var.get()


@contextmanager
def context_scope(
    *,
    user_id: str,
    user_role: str,
    request_id: str,
    session_id: Optional[str] = None,
    route: Optional[str] = None,
):
    """
    Context manager for setting a per-request SentinelContext.

    Usage:
        with context_scope(
            user_id="alice",
            user_role="operator",
            request_id="req_abc123",
            session_id="sess_99",
            route="TRACKING",
        ):
            result = graph.invoke(state)
    """
    token = _context_var.set(
        SentinelContext(
            user_id=user_id,
            user_role=user_role,
            request_id=request_id,
            session_id=session_id,
            route=route,
        )
    )
    try:
        yield
    finally:
        _context_var.reset(token)


# ===============================================================
# 2. GraphState — Mutable working memory per request
# ===============================================================

_graph_state_var: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar(
    "graph_state",
    default=None,
)


def set_graph_state(state: Dict[str, Any]) -> None:
    """Attach a GraphState dict to the current context."""
    _graph_state_var.set(state)


def get_graph_state() -> Dict[str, Any]:
    """Return the active GraphState dict (must have been set before)."""
    state = _graph_state_var.get()
    if state is None:
        raise RuntimeError("GraphState not set in this context.")
    return state

@contextmanager
def graph_state_scope(state: Dict[str, Any]):
    """
    Attach this GraphState for the duration of the block,
    then restore whatever was there before.
    """
    token = _graph_state_var.set(state)
    try:
        yield state
    finally:
        _graph_state_var.reset(token)