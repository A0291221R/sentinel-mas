"""
Comprehensive tests for crew_with_guard.py to achieve 100% code coverage.
This test file specifically targets the uncovered lines in the
finalize_error_node function.
"""

from typing import TYPE_CHECKING, Generator
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Import types for type checking
if TYPE_CHECKING:
    from sentinel_mas.agents.crew_with_guard import (
        finalize_error_node,
        post_tool_router,
        router_condition,
    )
    from sentinel_mas.state.graph_state import GraphState


# Mock dependencies before importing
@pytest.fixture(autouse=True)
def mock_all_dependencies() -> Generator[None, None, None]:
    """Mock all external dependencies before importing crew_with_guard modules"""
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

        # Import actual functions from crew_with_guard
        from sentinel_mas.agents.crew_with_guard import (
            finalize_error_node,
            post_tool_router,
            router_condition,
        )
        from sentinel_mas.state.graph_state import GraphState

        # Make them available globally for tests
        globals()["finalize_error_node"] = finalize_error_node
        globals()["post_tool_router"] = post_tool_router
        globals()["router_condition"] = router_condition
        globals()["GraphState"] = GraphState

        yield


class TestFinalizeErrorNodeCoverage:
    """Tests specifically designed to cover all branches in finalize_error_node"""

    def test_finalize_error_with_string_json_decode_success(self) -> None:
        """
        Test finalize_error_node with valid JSON string content.
        This covers the path: isinstance(raw, str) -> json.loads succeeds
        Lines 87-88, 92-94
        """
        tool_message = ToolMessage(
            content='{"status": "DENIED", "msg": "Custom denial message"}',
            tool_call_id="test_001",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert isinstance(final_msg, AIMessage)
        assert "Custom denial message" in final_msg.content
        assert final_msg.name == "system"

    def test_finalize_error_with_string_json_decode_error(self) -> None:
        """
        Test finalize_error_node with invalid JSON string content.
        This covers the path: isinstance(raw, str) -> json.JSONDecodeError exception
        Lines 92-97
        """
        tool_message = ToolMessage(
            content="This is not valid JSON {{{",
            tool_call_id="test_002",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert isinstance(final_msg, AIMessage)
        # Should fall through to default error message since JSON decode failed
        assert isinstance(final_msg.content, str)
        assert "internal error occurred" in final_msg.content.lower()

    def test_finalize_error_with_string_valid_json_denied(self) -> None:
        """
        Test finalize_error_node with valid JSON string that has DENIED status.
        This tests the string path that successfully parses and has status.
        """
        tool_message = ToolMessage(
            content='{"status": "DENIED", "msg": "Access restricted"}',
            tool_call_id="test_003",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert isinstance(final_msg, AIMessage)
        assert "Access restricted" in final_msg.content

    def test_finalize_error_with_string_valid_json_error(self) -> None:
        """
        Test finalize_error_node with valid JSON string that has ERROR status.
        """
        tool_message = ToolMessage(
            content='{"status": "ERROR", "msg": "Database connection failed"}',
            tool_call_id="test_004",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert isinstance(final_msg, AIMessage)
        assert "Database connection failed" in final_msg.content

    def test_finalize_error_denied_status_with_msg_field(self) -> None:
        """
        Test DENIED status with custom msg field (not message).
        This covers lines 101-106 with payload.get("msg")
        """
        tool_message = ToolMessage(
            content='{"status": "DENIED", '
            '"msg": "You lack permission for this operation"}',
            tool_call_id="test_005",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "You lack permission for this operation" in final_msg.content

    def test_finalize_error_denied_status_without_msg_field(self) -> None:
        """
        Test DENIED status without msg field, should use default message.
        This covers the 'or' clause in lines 103-106
        """
        tool_message = ToolMessage(
            content='{"status": "DENIED"}',
            tool_call_id="test_006",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        # The source uses backslash continuation which preserves whitespace
        assert "Access denied" in final_msg.content
        assert "not allowed" in final_msg.content
        assert "retrieve that information" in final_msg.content

    def test_finalize_error_error_status_with_msg_field(self) -> None:
        """
        Test ERROR status with custom msg field.
        This covers lines 107-112 with payload.get("msg")
        """
        tool_message = ToolMessage(
            content='{"status": "ERROR", "msg": "Network timeout occurred"}',
            tool_call_id="test_007",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "Network timeout occurred" in final_msg.content

    def test_finalize_error_error_status_without_msg_field(self) -> None:
        """
        Test ERROR status without msg field, should use default message.
        This covers the 'or' clause in lines 108-112
        """
        tool_message = ToolMessage(
            content='{"status": "ERROR"}',
            tool_call_id="test_008",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        # The source uses backslash continuation which preserves whitespace
        assert "could not be completed" in final_msg.content
        assert "internal error" in final_msg.content

    def test_finalize_error_with_no_tool_message(self) -> None:
        """
        Test when there's no ToolMessage in messages.
        """
        state: GraphState = {
            "messages": [
                HumanMessage(content="test query"),
                AIMessage(content="some response"),
            ],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "An internal error occurred" in final_msg.content

    def test_finalize_error_with_malformed_content(self) -> None:
        """
        Test finalize_error_node with content that will trigger exception.
        This tests the exception handler at line 113-114.
        """
        # Create a ToolMessage with content that looks like JSON but has wrong structure
        tool_message = ToolMessage(
            content='{"unexpected": "structure", "no_status": true}',
            tool_call_id="test_009",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        # Should use default error message since there's no recognized status
        assert "An internal error occurred" in final_msg.content

    def test_finalize_error_with_empty_json_string(self) -> None:
        """
        Test with empty JSON string.
        """
        tool_message = ToolMessage(
            content="{}",
            tool_call_id="test_010",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "An internal error occurred" in final_msg.content

    def test_finalize_error_with_json_array_string(self) -> None:
        """
        Test with JSON array string (not an object).
        This tests the case where JSON parses but payload.get() won't work.
        """
        tool_message = ToolMessage(
            content='["error1", "error2"]',
            tool_call_id="test_011",
        )

        state: GraphState = {
            "messages": [HumanMessage(content="test query"), tool_message],
            "user_question": "test question",
        }

        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        # Array doesn't have .get() method, triggers exception handler
        assert "An internal error occurred" in final_msg.content


class TestPostToolRouterCoverage:
    """Tests for post_tool_router function"""

    def test_post_tool_router_halt_true(self) -> None:
        """Test when halt is True"""
        state: GraphState = {
            "messages": [],
            "user_question": "",
            "halt": True,
        }

        result = post_tool_router(state)
        assert result == "HALT"

    def test_post_tool_router_halt_false(self) -> None:
        """Test when halt is False"""
        state: GraphState = {
            "messages": [],
            "user_question": "",
            "halt": False,
        }

        result = post_tool_router(state)
        assert result == "CONTINUE"

    def test_post_tool_router_halt_missing(self) -> None:
        """Test when halt key is missing (should default to False)"""
        state: GraphState = {
            "messages": [],
            "user_question": "",
        }

        result = post_tool_router(state)
        assert result == "CONTINUE"


class TestRouterConditionCoverage:
    """Tests for router_condition function"""

    def test_router_condition_with_string_json(self) -> None:
        """Test router_condition with JSON string content"""
        ai_message = AIMessage(
            content='{"route": "EVENTS", "confidence": 0.9, "reason": "event query"}'
        )

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "EVENTS"

    def test_router_condition_with_string_json_sop(self) -> None:
        """Test router_condition with SOP route as JSON string"""
        ai_message = AIMessage(
            content='{"route": "SOP", "confidence": 0.85, "reason": "SOP query"}'
        )

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "SOP"

    def test_router_condition_with_tracking_route(self) -> None:
        """Test router_condition with TRACKING route"""
        ai_message = AIMessage(
            content='{"route": "tracking", "confidence": 0.8, "reason": "track person"}'
        )

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "TRACKING"  # Should be uppercased

    def test_router_condition_with_invalid_route(self) -> None:
        """Test router_condition with invalid route name"""
        ai_message = AIMessage(
            content='{"route": "INVALID", "confidence": 0.9, "reason": "unknown"}'
        )

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "__end__"

    def test_router_condition_with_invalid_json(self) -> None:
        """Test router_condition with invalid JSON"""
        ai_message = AIMessage(content="not json at all")

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "__end__"

    def test_router_condition_with_missing_route_key(self) -> None:
        """Test router_condition with valid JSON but missing route key"""
        ai_message = AIMessage(content='{"confidence": 0.9, "reason": "test"}')

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "__end__"

    def test_router_condition_with_empty_route(self) -> None:
        """Test router_condition with empty route string"""
        ai_message = AIMessage(
            content='{"route": "", "confidence": 0.9, "reason": "test"}'
        )

        state: GraphState = {
            "messages": [ai_message],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "__end__"

    def test_router_condition_with_no_ai_message(self) -> None:
        """Test router_condition when there's no AIMessage"""
        state: GraphState = {
            "messages": [HumanMessage(content="test query")],
            "user_question": "test question",
        }

        result = router_condition(state)
        assert result == "__end__"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=sentinel_mas.agents.crew_with_guard"])
