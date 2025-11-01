import json

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END
from sentinel_mas.agents.crew_with_guard import (
    finalize_error_node,
    post_tool_router,
    router_condition,
)


def test_router_condition_sets_route_and_returns_branch() -> None:
    state = {
        "messages": [
            AIMessage(content=json.dumps({"route": "EVENTS", "confidence": 0.9}))
        ]
    }
    branch = router_condition(state)
    assert branch == "EVENTS"
    assert state["route"] == "EVENTS"
    assert state["router_decision"]["confidence"] == 0.9


def test_post_tool_router_uses_state_route_or_fallback() -> None:
    assert post_tool_router({"halt": False}) == "CONTINUE"
    assert post_tool_router({"halt": True}) == "HALT"


def test_finalize_error_node_wraps_error() -> None:
    state = {
        "messages": [
            ToolMessage(content="Boom", tool_call_id="toolcall-123", name="test-error")
        ]
    }
    out = finalize_error_node(state)
    # Expect a safe message or a flag in state
    assert out.get("messages")


def test_router_condition_handles_bad_json_fallback() -> None:
    # If content is not JSON, function should not crash; returns default branch or None
    state = {"messages": [AIMessage(content="not-json")]}
    branch = router_condition(state)
    assert branch in (END, "SOP", "EVENTS", "TRACKING")
