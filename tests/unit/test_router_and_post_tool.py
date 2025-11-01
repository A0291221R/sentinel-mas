import json
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END

if TYPE_CHECKING:
    from sentinel_mas.agents.crew import (
        finalize_error_node,
        post_tool_router,
        router_condition,
    )
    from sentinel_mas.state.graph_state import GraphState


# Mock at the crew_agents level where ChatOpenAI is actually used
@pytest.fixture(autouse=True)
def mock_all_dependencies() -> Generator[None, None, None]:
    """Mock all external dependencies before importing crew modules"""
    with (
        patch("sentinel_mas.agents.crew_agents.ChatOpenAI") as mock_chat_openai,
        patch("sentinel_mas.agents.crew_agents.AGENT_REGISTRY") as mock_registry,
    ):

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_chat_openai.return_value = mock_llm_instance

        # Mock agent registry
        mock_runtime = MagicMock()
        mock_runtime.llm_model = "gpt-4o-mini"
        mock_runtime.llm_temperature = 0.0
        mock_runtime.llm_max_tokens = 300
        mock_runtime.system_prompt = "Test prompt"
        mock_runtime.tools = {}
        mock_registry.__getitem__.return_value = mock_runtime

        # Now import your actual functions
        from sentinel_mas.agents.crew import (
            finalize_error_node,
            parse_time_node,
            post_tool_router,
            router_condition,
        )
        from sentinel_mas.state.graph_state import GraphState

        # Make them available globally for the tests
        globals()["router_condition"] = router_condition
        globals()["parse_time_node"] = parse_time_node
        globals()["GraphState"] = GraphState
        globals()["post_tool_router"] = post_tool_router
        globals()["finalize_error_node"] = finalize_error_node

        yield


def test_router_condition_sets_route_and_returns_branch() -> None:
    state: GraphState = {
        "messages": [
            AIMessage(content=json.dumps({"route": "EVENTS", "confidence": 0.9}))
        ],
        "user_question": "",
    }
    branch = router_condition(state)
    assert branch == "EVENTS"
    assert isinstance(state, dict)

    state_map: GraphState | dict[str, Any]
    if isinstance(state, str):
        state_map = json.loads(state)
    else:
        state_map = state

    route = state_map.get("route")
    assert isinstance(route, str)
    assert route == "EVENTS"

    router_decision = state_map.get("router_decision")
    assert isinstance(router_decision, dict)
    assert router_decision.get("confidence") == 0.9


def test_post_tool_router_uses_state_route_or_fallback() -> None:
    state: GraphState = {
        "messages": [],
        "user_question": "",
    }
    assert post_tool_router({**state, "halt": False}) == "CONTINUE"
    assert post_tool_router({**state, "halt": True}) == "HALT"


def test_finalize_error_node_wraps_error() -> None:
    state: GraphState = {
        "messages": [
            ToolMessage(content="Boom", tool_call_id="toolcall-123", name="test-error")
        ],
        "user_question": "test tool error",
    }
    out = finalize_error_node(state)
    # Expect a safe message or a flag in state
    assert out.get("messages")


def test_router_condition_handles_bad_json_fallback() -> None:
    # If content is not JSON, function should not crash; returns default branch or None
    state: GraphState = {
        "messages": [AIMessage(content="not-json")],
        "user_question": "",
    }
    branch = router_condition(state)
    assert branch in (END, "SOP", "EVENTS", "TRACKING")
