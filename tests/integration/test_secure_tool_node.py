import pytest
import json
from unittest.mock import Mock, patch, MagicMock, ANY
from langchain_core.messages import AIMessage, ToolMessage

# Import the runtime components
from sentinel_mas.policy_sentinel.runtime import SentinelContext
from sentinel_mas.policy_sentinel.secure_tool_node import SecureToolNode

pytestmark = pytest.mark.integration

class TestSecureToolNode:
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools for testing"""
        tool1 = Mock()
        tool1.name = "test_tool_1"
        tool1.invoke = Mock(return_value={"result": "success"})
        
        tool2 = Mock() 
        tool2.name = "test_tool_2"
        tool2.invoke = Mock(return_value={"count": 5})
        
        return [tool1, tool2]
    
    @pytest.fixture
    def sample_state(self):
        """Sample state for testing"""
        return {
            "user_id": "test_user",
            "user_role": "operator", 
            "request_id": "test_req_123",
            "session_id": "test_sess_456",
            "route": "TRACKING",
            "user_question": "Test question",
            "messages": [],
            "audit_trail": []
        }
    
    @pytest.fixture
    def secure_tool_node(self, mock_tools):
        """Create SecureToolNode instance for testing"""
        return SecureToolNode(
            route="TRACKING",
            tools=mock_tools,
            agent_name="test_agent"
        )
    
    def test_initialization(self, mock_tools):
        """Test SecureToolNode initialization"""
        node = SecureToolNode(
            route="TRACKING", 
            tools=mock_tools,
            agent_name="test_agent"
        )
        
        assert node.route == "TRACKING"
        assert node.agent_name == "test_agent"
        assert "test_tool_1" in node.tools
        assert "test_tool_2" in node.tools
    
    def test_initialization_missing_tool_name(self):
        """Test initialization fails with tools missing names"""
        bad_tool = Mock()
        # Remove name attribute to simulate bad tool
        delattr(bad_tool, 'name')
        
        with pytest.raises(ValueError, match="Tool must have .name or __name__"):
            SecureToolNode(route="TRACKING", tools=[bad_tool])
    
    def test_get_route_from_state(self, mock_tools):
        """Test route extraction from state"""
        node = SecureToolNode(
            route="DEFAULT",
            tools=mock_tools,
            route_from_state=True
        )
        
        # Test with route in state
        state_with_route = {"route": "EVENTS"}
        assert node._get_route(state_with_route) == "EVENTS"
        
        # Test with router_decision
        state_with_decision = {"router_decision": {"route": "SOP"}}
        assert node._get_route(state_with_decision) == "SOP"
        
        # Test fallback to default
        state_empty = {}
        assert node._get_route(state_empty) == "DEFAULT"
    
    def test_last_ai_message_extraction(self, secure_tool_node, sample_state):
        """Test extracting last AI message with tool calls"""
        # Create messages with AI message containing tool calls
        tool_calls = [
            {
                "name": "test_tool_1",
                "args": {"param": "value"},
                "id": "call_1",
                "type": "tool_call"
            }
        ]
        
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        last_ai = secure_tool_node._last_ai(sample_state["messages"])
        assert last_ai == ai_message
        assert last_ai.tool_calls == tool_calls
    
    def test_last_ai_no_tool_calls(self, secure_tool_node, sample_state):
        """Test when no AI message with tool calls exists"""
        # Messages without AI message
        sample_state["messages"] = []
        assert secure_tool_node._last_ai(sample_state["messages"]) is None
        
        # AI message without tool calls
        ai_message = AIMessage(content="No tool calls")
        sample_state["messages"] = [ai_message]
        assert secure_tool_node._last_ai(sample_state["messages"]) == ai_message
    
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.context_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.graph_state_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.get_graph_state')
    def test_successful_tool_execution(
        self, mock_get_graph_state, mock_tool_registry, mock_secure_execute, mock_graph_scope, mock_context_scope, 
        secure_tool_node, sample_state, mock_tools
    ):
        """Test successful tool execution flow"""
        # Mock TOOL_REGISTRY to return our mock tool
        mock_tool_registry.get.return_value = mock_tools[0]
        
        # Mock the context managers to return the actual state
        mock_context_scope.return_value.__enter__ = Mock(return_value=None)
        mock_context_scope.return_value.__exit__ = Mock(return_value=None)
        mock_graph_scope.return_value.__enter__ = Mock(return_value=sample_state)
        mock_graph_scope.return_value.__exit__ = Mock(return_value=None)
        
        # Mock get_graph_state to return our sample state
        mock_get_graph_state.return_value = sample_state
        
        # Mock secure_execute_tool to return success
        mock_secure_execute.return_value = {"data": "success_result"}
        
        # Create state with AI message containing tool calls
        tool_calls = [
            {
                "name": "test_tool_1",
                "args": {"param": "value"},
                "id": "call_1",
                "type": "tool_call"
            }
        ]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        # Execute the node
        result = secure_tool_node(sample_state)
        
        # Verify results
        assert "messages" in result

        # AIMessage + ToolMessage
        assert len(result["messages"]) == 2
        assert isinstance(result["messages"][-1], ToolMessage)
        
        # Verify tool message content
        tool_message = result["messages"][-1]
        content = json.loads(tool_message.content)
        assert content["ok"] is True
        assert content["status"] == "OK"
        assert content["data"] == {"data": "success_result"}
        
        # Verify secure_execute_tool was called correctly
        mock_secure_execute.assert_called_once_with(
            tool_name="test_tool_1",
            tool_fn=mock_tools[0],  # Should be the tool from TOOL_REGISTRY
            tool_args={"param": "value"}
        )
        
        # Verify TOOL_REGISTRY was queried
        mock_tool_registry.get.assert_called_once_with("test_tool_1")
    
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.context_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.graph_state_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.get_graph_state')
    def test_permission_denied_tool_execution(
        self, mock_get_graph_state, mock_tool_registry, mock_secure_execute, mock_graph_scope, mock_context_scope,
        secure_tool_node, sample_state, mock_tools
    ):
        """Test tool execution when permission is denied"""
        # Mock TOOL_REGISTRY to return our mock tool
        mock_tool_registry.get.return_value = mock_tools[0]
        
        # Mock context managers
        mock_context_scope.return_value.__enter__ = Mock(return_value=None)
        mock_context_scope.return_value.__exit__ = Mock(return_value=None)
        mock_graph_scope.return_value.__enter__ = Mock(return_value=sample_state)
        mock_graph_scope.return_value.__exit__ = Mock(return_value=None)
        
        # Mock get_graph_state to return our sample state
        mock_get_graph_state.return_value = sample_state
        
        # Mock secure_execute_tool to raise PermissionError
        mock_secure_execute.side_effect = PermissionError("Not allowed")
        
        # Create state with AI message containing tool calls
        tool_calls = [
            {
                "name": "test_tool_1", 
                "args": {"param": "value"},
                "id": "call_1",
                "type": "tool_call"
            }
        ]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        # Execute the node
        result = secure_tool_node(sample_state)
        
        # Verify results - should have halt=True and error message
        assert result["halt"] is True
        
        tool_message = result["messages"][-1]
        content = json.loads(tool_message.content)
        assert content["ok"] is False
        assert content["status"] == "DENIED"
        assert "PermissionError" in content["error_type"]
        
        # Verify secure_execute_tool was called correctly
        mock_secure_execute.assert_called_once_with(
            tool_name="test_tool_1",
            tool_fn=mock_tools[0],  # Should be the tool from TOOL_REGISTRY
            tool_args={"param": "value"}
        )
    
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.context_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.graph_state_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.get_graph_state')
    def test_tool_execution_failure(
        self, mock_get_graph_state, mock_tool_registry, mock_secure_execute, mock_graph_scope, mock_context_scope,
        secure_tool_node, sample_state, mock_tools
    ):
        """Test tool execution when tool fails"""
        # Mock TOOL_REGISTRY to return our mock tool
        mock_tool_registry.get.return_value = mock_tools[0]
        
        # Mock context managers
        mock_context_scope.return_value.__enter__ = Mock(return_value=None)
        mock_context_scope.return_value.__exit__ = Mock(return_value=None)
        mock_graph_scope.return_value.__enter__ = Mock(return_value=sample_state)
        mock_graph_scope.return_value.__exit__ = Mock(return_value=None)
        
        # Mock get_graph_state to return our sample state
        mock_get_graph_state.return_value = sample_state
        
        # Mock secure_execute_tool to raise ValueError
        mock_secure_execute.side_effect = ValueError("Invalid parameter")
        
        # Create state with AI message containing tool calls
        tool_calls = [
            {
                "name": "test_tool_1",
                "args": {"param": "invalid"},
                "id": "call_1",
                "type": "tool_call"
            }
        ]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        # Execute the node
        result = secure_tool_node(sample_state)
        
        # Verify results - should have halt=True and error message
        assert result["halt"] is True
        
        tool_message = result["messages"][-1]
        content = json.loads(tool_message.content)
        assert content["ok"] is False
        assert content["status"] == "BAD_REQUEST"
        assert "ValueError" in content["error_type"]
        
        # Verify secure_execute_tool was called correctly
        mock_secure_execute.assert_called_once_with(
            tool_name="test_tool_1",
            tool_fn=mock_tools[0],  # Should be the tool from TOOL_REGISTRY
            tool_args={"param": "invalid"}
        )
    
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.context_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.graph_state_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.get_graph_state')
    def test_unknown_tool(
        self, mock_get_graph_state, mock_tool_registry, mock_graph_scope, mock_context_scope, 
        secure_tool_node, sample_state
    ):
        """Test handling of unknown/hallucinated tools"""
        # Mock TOOL_REGISTRY to return None (unknown tool)
        mock_tool_registry.get.return_value = None
        
        # Mock context managers
        mock_context_scope.return_value.__enter__ = Mock(return_value=None)
        mock_context_scope.return_value.__exit__ = Mock(return_value=None)
        mock_graph_scope.return_value.__enter__ = Mock(return_value=sample_state)
        mock_graph_scope.return_value.__exit__ = Mock(return_value=None)
        
        # Mock get_graph_state to return our sample state
        mock_get_graph_state.return_value = sample_state
        
        # Create state with AI message calling unknown tool
        tool_calls = [
            {
                "name": "unknown_tool",  # Tool not in our registry
                "args": {"param": "value"},
                "id": "call_1",
                "type": "tool_call"
            }
        ]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        # Execute the node
        result = secure_tool_node(sample_state)
        
        # Verify results - should have error message for unknown tool
        tool_message = result["messages"][-1]
        content = json.loads(tool_message.content)
        assert content["ok"] is False
        assert content["status"] == "DENIED"
        assert "UnknownTool" in content["error_type"]
        assert "not registered" in content["msg"]
        
        # Verify TOOL_REGISTRY was queried
        mock_tool_registry.get.assert_called_once_with("unknown_tool")
    
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.context_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.graph_state_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.get_graph_state')
    def test_multiple_tool_executions(
        self, mock_get_graph_state, mock_tool_registry, mock_secure_execute, mock_graph_scope, mock_context_scope,
        secure_tool_node, sample_state, mock_tools
    ):
        """Test execution of multiple tools in one call"""
        # Mock TOOL_REGISTRY to return appropriate tools
        def tool_registry_side_effect(tool_name):
            if tool_name == "test_tool_1":
                return mock_tools[0]
            elif tool_name == "test_tool_2":
                return mock_tools[1]
            return None
        
        mock_tool_registry.get.side_effect = tool_registry_side_effect
        
        # Mock context managers
        mock_context_scope.return_value.__enter__ = Mock(return_value=None)
        mock_context_scope.return_value.__exit__ = Mock(return_value=None)
        mock_graph_scope.return_value.__enter__ = Mock(return_value=sample_state)
        mock_graph_scope.return_value.__exit__ = Mock(return_value=None)
        
        # Mock get_graph_state to return our sample state
        mock_get_graph_state.return_value = sample_state
        
        # Setup different return values for different tools
        def secure_execute_side_effect(tool_name, tool_fn, tool_args):
            if tool_name == "test_tool_1":
                return {"result": "from_tool_1"}
            elif tool_name == "test_tool_2":
                return {"count": 42}
        
        mock_secure_execute.side_effect = secure_execute_side_effect
        
        # Create state with multiple tool calls
        tool_calls = [
            {
                "name": "test_tool_1",
                "args": {"param1": "value1"},
                "id": "call_1",
                "type": "tool_call"
            },
            {
                "name": "test_tool_2", 
                "args": {"param2": "value2"},
                "id": "call_2",
                "type": "tool_call"
            }
        ]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        # Execute the node
        result = secure_tool_node(sample_state)
        
        # Verify results - should have multiple tool messages
        # 1 AIMessage + 2 ToolMessages
        assert len(result["messages"]) == 3
        assert result["halt"] is False  # No failures
        
        # Verify both tools were executed
        assert mock_secure_execute.call_count == 2
        
        # Verify TOOL_REGISTRY was queried for both tools
        assert mock_tool_registry.get.call_count == 2
        mock_tool_registry.get.assert_any_call("test_tool_1")
        mock_tool_registry.get.assert_any_call("test_tool_2")
    
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.context_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.graph_state_scope')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY')
    @patch('sentinel_mas.policy_sentinel.secure_tool_node.get_graph_state')
    def test_mixed_success_and_failure(
        self, mock_get_graph_state, mock_tool_registry, mock_secure_execute, mock_graph_scope, mock_context_scope,
        secure_tool_node, sample_state, mock_tools
    ):
        """Test mixed success and failure in multiple tool executions"""
        # Mock TOOL_REGISTRY to return appropriate tools
        def tool_registry_side_effect(tool_name):
            if tool_name == "test_tool_1":
                return mock_tools[0]
            elif tool_name == "test_tool_2":
                return mock_tools[1]
            return None
        
        mock_tool_registry.get.side_effect = tool_registry_side_effect
        
        # Mock context managers
        mock_context_scope.return_value.__enter__ = Mock(return_value=None)
        mock_context_scope.return_value.__exit__ = Mock(return_value=None)
        mock_graph_scope.return_value.__enter__ = Mock(return_value=sample_state)
        mock_graph_scope.return_value.__exit__ = Mock(return_value=None)
        
        # Mock get_graph_state to return our sample state
        mock_get_graph_state.return_value = sample_state
        
        # Setup mixed results
        def secure_execute_side_effect(tool_name, tool_fn, tool_args):
            if tool_name == "test_tool_1":
                return {"success": True}
            elif tool_name == "test_tool_2":
                raise PermissionError("Not allowed for tool_2")
        
        mock_secure_execute.side_effect = secure_execute_side_effect
        
        # Create state with multiple tool calls
        tool_calls = [
            {
                "name": "test_tool_1",
                "args": {},
                "id": "call_1",
                "type": "tool_call"
            },
            {
                "name": "test_tool_2",
                "args": {},
                "id": "call_2",
                "type": "tool_call"
            }
        ]
        ai_message = AIMessage(content="", tool_calls=tool_calls)
        sample_state["messages"] = [ai_message]
        
        # Execute the node
        result = secure_tool_node(sample_state)
        
        # Verify results - should have mixed messages and halt due to failure
        # 1 AIMessage + 2 ToolMessage
        assert len(result["messages"]) == 3
        assert result["halt"] is True  # Halt due to permission error
        
        # Check first message (success)
        msg1_content = json.loads(result["messages"][-2].content)
        assert msg1_content["ok"] is True
        
        # Check second message (failure)  
        msg2_content = json.loads(result["messages"][-1].content)
        assert msg2_content["ok"] is False
        assert msg2_content["status"] == "DENIED"
    
    def test_state_overrides(self, secure_tool_node):
        """Test state override functionality"""
        args = {"start_ms": 1000, "end_ms": 2000, "location_id": "loc_123"}
        state = {
            "start_ms": 5000,
            "end_ms": 6000, 
            "location_id": "loc_456",
            "other_field": "ignored"
        }
        
        # Test without freeze_time_window (should not override)
        secure_tool_node.freeze_time_window = False
        result = secure_tool_node._state_overrides(args.copy(), state)
        assert result["start_ms"] == 1000  # Original value
        assert result["end_ms"] == 2000    # Original value
        
        # Test with freeze_time_window (should override time fields)
        secure_tool_node.freeze_time_window = True
        secure_tool_node.override_keys = {"location_id"}
        result = secure_tool_node._state_overrides(args.copy(), state)
        assert result["start_ms"] == 5000  # Overridden from state
        assert result["end_ms"] == 6000    # Overridden from state  
        assert result["location_id"] == "loc_456"  # Overridden from override_keys
    
    def test_empty_tool_calls(self, secure_tool_node, sample_state):
        """Test behavior when no tool calls are present"""
        # AI message without tool_calls
        ai_message = AIMessage(content="No tool calls here")
        sample_state["messages"] = [ai_message]
        
        result = secure_tool_node(sample_state)
        
        # Should return empty state modifications
        assert result == {}