# test_workflows.py
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import json

pytestmark = pytest.mark.integration

class TestWorkflowScenarios:
    """End-to-end workflow tests for different user scenarios"""
    
    @patch('sentinel_mas.agents.crew.CrewAgent')
    @patch('sentinel_mas.agents.crew.SecureToolNode')
    @patch('sentinel_mas.agents.crew.ToolNode')
    def test_router_workflow(self, mock_tool_node, mock_secure_tool_node, mock_crew_agent):
        """Test router decision making"""
        # Mock agent responses
        mock_agent_instance = MagicMock()
        mock_crew_agent.return_value = mock_agent_instance
        
        # Import after mocking
        from sentinel_mas.agents.crew import router_condition
        
        # Test SOP routing
        state = {
            "messages": [AIMessage(content='{"route": "SOP", "confidence": 0.9, "reason": "procedure"}')],
            "user_question": "How to handle fire?"
        }
        
        result = router_condition(state)
        assert result == "SOP"
        
        # Test EVENTS routing
        state = {
            "messages": [AIMessage(content='{"route": "EVENTS", "confidence": 0.8, "reason": "events"}')],
            "user_question": "Who entered zone A?"
        }
        
        result = router_condition(state)
        assert result == "EVENTS"
    
    @patch('sentinel_mas.agents.crew.resolve_time_window')
    def test_time_parsing_integration(self, mock_resolve_time):
        """Test time parsing integration"""
        mock_resolve_time.return_value = (1704067200000, 1704070800000, "last hour")
        
        from sentinel_mas.agents.crew import parse_time_node
        
        state = {
            "user_question": "Show events from last hour",
            "messages": [HumanMessage(content="Show events from last hour")]
        }
        
        result = parse_time_node(state)
        
        assert result["start_ms"] == 1704067200000
        assert result["end_ms"] == 1704070800000
        assert result["time_label"] == "last hour"