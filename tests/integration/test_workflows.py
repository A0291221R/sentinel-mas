# test_workflows.py
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from sentinel_mas.state.graph_state import GraphState

pytestmark = pytest.mark.integration


class TestWorkflowScenarios:
    """End-to-end workflow tests for different user scenarios"""

    @patch("sentinel_mas.agents.crew_with_guard.CrewAgent")
    @patch("sentinel_mas.agents.crew_with_guard.SecureToolNode")
    def test_router_workflow(
        self,
        mock_secure_tool_node: MagicMock,
        mock_crew_agent: MagicMock,
    ) -> None:
        """Test router decision making"""
        # Mock agent responses
        mock_agent_instance = MagicMock()
        mock_crew_agent.return_value = mock_agent_instance

        # Import after mocking
        from sentinel_mas.agents.crew_with_guard import router_condition

        # Test SOP routing
        state: GraphState = {
            "messages": [
                AIMessage(
                    content='{"route": "SOP", "confidence": 0.9, "reason": "procedure"}'
                )
            ],
            "user_question": "How to handle fire?",
        }

        result = router_condition(state)
        assert result == "SOP"

        # Test EVENTS routing
        state = {
            "messages": [
                AIMessage(
                    content='{"route": "EVENTS", "confidence": 0.8, "reason": "events"}'
                )
            ],
            "user_question": "Who entered zone A?",
        }

        result = router_condition(state)
        assert result == "EVENTS"

    @patch("sentinel_mas.agents.crew_with_guard.resolve_time_window")
    def test_time_parsing_integration(self, mock_resolve_time: MagicMock) -> None:
        """Test time parsing integration"""
        mock_resolve_time.return_value = (1704067200000, 1704070800000, "last hour")

        from sentinel_mas.agents.crew_with_guard import parse_time_node

        state: GraphState = {
            "user_question": "Show events from last hour",
            "messages": [HumanMessage(content="Show events from last hour")],
        }

        result = parse_time_node(state)

        assert result["start_ms"] == 1704067200000
        assert result["end_ms"] == 1704070800000
        assert result["time_label"] == "last hour"
