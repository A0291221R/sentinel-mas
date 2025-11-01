# tests/test_crew_integration_fixed.py
import json
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END

pytestmark = pytest.mark.integration


# Mock at the crew_agents level where ChatOpenAI is actually used
@pytest.fixture(autouse=True)
def mock_all_dependencies() -> Generator[None, None, None]:
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
        global router_condition, parse_time_node
        from sentinel_mas.agents.crew import parse_time_node, router_condition

        yield


class TestCrewIntegration:
    """Integration tests using YOUR actual functions"""

    def test_router_condition_valid_routes(self) -> None:
        """Test YOUR router_condition function with valid route decisions"""
        test_cases = [
            (
                '{"route": "SOP", "confidence": 0.9, "reason": "procedure question"}',
                "SOP",
            ),
            (
                '{"route": "EVENTS", "confidence": 0.8, "reason": "event query"}',
                "EVENTS",
            ),
            (
                '{"route": "TRACKING", "confidence": 0.7, "reason": "tracking request"}',
                "TRACKING",
            ),
        ]

        for ai_content, expected_route in test_cases:
            state = {
                "messages": [AIMessage(content=ai_content)],
                "user_question": "test question",
            }

            # Call YOUR actual function
            result = router_condition(state)
            assert result == expected_route
            assert state["route"] == expected_route

    def test_router_condition_invalid_cases(self) -> None:
        """Test YOUR router_condition function with invalid inputs"""
        invalid_cases = [
            '{"route": "INVALID", "confidence": 0.9, "reason": "test"}',
            "not json at all",
            '{"wrong_key": "value"}',
            "",
        ]

        for ai_content in invalid_cases:
            state = {
                "messages": [AIMessage(content=ai_content)],
                "user_question": "test question",
            }

            # Call YOUR actual function
            result = router_condition(state)
            assert result == END

    @patch("sentinel_mas.agents.crew.resolve_time_window")
    def test_parse_time_node_success(self, mock_resolve_time: MagicMock) -> None:
        """Test YOUR parse_time_node function with successful parsing"""
        # Mock the time resolution
        mock_resolve_time.return_value = (
            1704067200000,
            1704070800000,
            "last 30 minutes",
        )

        state = {"user_question": "Show events from yesterday 2pm to 4pm"}

        # Call YOUR actual function
        result = parse_time_node(state)

        assert "start_ms" in result
        assert "end_ms" in result
        assert "time_label" in result
        assert result["start_ms"] == 1704067200000
        assert result["end_ms"] == 1704070800000

    def test_parse_time_node_already_parsed(self) -> None:
        """Test YOUR parse_time_node when times already exist"""
        state = {
            "user_question": "test question",
            "start_ms": 1704067200000,
            "end_ms": 1704070800000,
        }

        # Call YOUR actual function
        result = parse_time_node(state)
        assert result == state

    @patch("sentinel_mas.agents.crew.resolve_time_window")
    def test_parse_time_node_failure(self, mock_resolve_time: MagicMock) -> None:
        """Test YOUR parse_time_node function when parsing fails"""
        mock_resolve_time.side_effect = Exception("Parse failed")

        state = {"user_question": "this won't parse"}

        # Call YOUR actual function
        result = parse_time_node(state)
        assert result == {}
