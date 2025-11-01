import json
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


# Mock at the crew_agents level where ChatOpenAI is actually used
@pytest.fixture(autouse=True)
def mock_all_dependencies() -> Generator [None, None, None]:
    """Mock all external dependencies before importing crew modules"""
    with patch("sentinel_mas.agents.crew_agents.ChatOpenAI") as mock_chat_openai, patch(
        "sentinel_mas.agents.crew_agents.AGENT_REGISTRY"
    ) as mock_registry:

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
        global post_tool_router, finalize_error_node
        from sentinel_mas.agents.crew import finalize_error_node, post_tool_router

        yield


class TestToolSecurity:
    """Tests for YOUR tool security and error handling functions"""

    def test_post_tool_router_continue(self) -> None:
        """Test YOUR post_tool_router function for continue case"""
        state = {"halt": False}

        # Call YOUR actual function
        result = post_tool_router(state)
        assert result == "CONTINUE"

    def test_post_tool_router_halt(self) -> None:
        """Test YOUR post_tool_router function for halt case"""
        state = {"halt": True}

        # Call YOUR actual function
        result = post_tool_router(state)
        assert result == "HALT"

    def test_finalize_error_node_denied(self) -> None:
        """Test YOUR finalize_error_node function for denied case"""
        denied_message = ToolMessage(
            content=json.dumps({"status": "DENIED", "message": "Access denied"}),
            tool_call_id="test_123",
        )

        state = {
            "messages": [HumanMessage(content="test"), denied_message],
            "user_question": "test question",
        }

        # Call YOUR actual function
        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "Access denied" in final_msg.content
        assert final_msg.name == "system"

    def test_finalize_error_node_error(self) -> None:
        """Test YOUR finalize_error_node function for error case"""
        error_message = ToolMessage(
            content=json.dumps({"status": "ERROR", "message": "Internal error"}),
            tool_call_id="test_123",
        )

        state = {
            "messages": [HumanMessage(content="test"), error_message],
            "user_question": "test question",
        }

        # Call YOUR actual function
        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "internal error" in final_msg.content.lower()

    def test_finalize_error_node_generic(self) -> None:
        """Test YOUR finalize_error_node function for generic case"""
        state = {
            "messages": [HumanMessage(content="test")],
            "user_question": "test question",
        }

        # Call YOUR actual function
        result = finalize_error_node(state)

        assert "messages" in result
        final_msg = result["messages"][-1]
        assert "internal error occurred" in final_msg.content
