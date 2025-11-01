from unittest.mock import MagicMock, Mock, patch

import pytest

from sentinel_mas.policy_sentinel.secure_executor import (
    call_tool_safely,
    guard_tool_call,
    secure_execute_tool,
)


class TestSecureExecutor:

    def test_call_tool_safely_invoke(self) -> None:
        """Test call_tool_safely with .invoke() method"""
        mock_tool = Mock()
        mock_tool.invoke = Mock(return_value={"result": "success"})

        result = call_tool_safely(mock_tool, {"param": "value"})

        mock_tool.invoke.assert_called_once_with({"param": "value"})
        assert result == {"result": "success"}

    def test_call_tool_safely_run(self) -> None:
        """Test call_tool_safely with .run() method"""
        mock_tool = Mock()
        mock_tool.run = Mock(return_value={"result": "success"})
        # Remove invoke to test fallback to run
        delattr(mock_tool, "invoke")

        result = call_tool_safely(mock_tool, {"param": "value"})

        mock_tool.run.assert_called_once_with({"param": "value"})
        assert result == {"result": "success"}

    def test_call_tool_safely_callable(self) -> None:
        """Test call_tool_safely with plain callable"""

        def plain_function(param):
            return {"result": param}

        result = call_tool_safely(plain_function, {"param": "value"})

        assert result == {"result": "value"}

    @patch("sentinel_mas.policy_sentinel.secure_executor.guard_tool_call")
    @patch("sentinel_mas.policy_sentinel.secure_executor.audit_guard_allow")
    @patch("sentinel_mas.policy_sentinel.secure_executor.audit_tool_success")
    @patch("sentinel_mas.policy_sentinel.secure_executor.get_graph_state")
    def test_secure_execute_tool_success(
        self, mock_get_graph_state, mock_success, mock_allow, mock_guard
    ) -> None:
        """Test successful tool execution"""
        # Mock graph state to avoid RuntimeError
        mock_get_graph_state.return_value = {"user_question": "test"}

        # Mock tool function that uses .invoke()
        mock_tool = Mock()
        mock_tool.invoke = Mock(return_value={"result": "success"})

        result = secure_execute_tool(
            tool_name="test_tool", tool_fn=mock_tool, tool_args={"param": "value"}
        )

        mock_guard.assert_called_once_with(
            tool_name="test_tool", args={"param": "value"}, gate="tool_gate"
        )
        mock_allow.assert_called_once()
        mock_success.assert_called_once()
        mock_tool.invoke.assert_called_once_with({"param": "value"})
        assert result == {"result": "success"}

    @patch("sentinel_mas.policy_sentinel.secure_executor.guard_tool_call")
    @patch("sentinel_mas.policy_sentinel.secure_executor.audit_guard_allow")
    @patch("sentinel_mas.policy_sentinel.secure_executor.audit_tool_failure")
    @patch("sentinel_mas.policy_sentinel.secure_executor.get_graph_state")
    def test_secure_execute_tool_failure(
        self, mock_get_graph_state, mock_failure, mock_allow, mock_guard
    ) -> None:
        """Test tool execution failure"""
        # Mock graph state to avoid RuntimeError
        mock_get_graph_state.return_value = {"user_question": "test"}

        # Mock tool function that raises exception and uses .invoke()
        mock_tool = Mock()
        mock_tool.invoke = Mock(side_effect=ValueError("Tool failed"))

        with pytest.raises(ValueError):
            secure_execute_tool(
                tool_name="test_tool", tool_fn=mock_tool, tool_args={"param": "value"}
            )

        mock_guard.assert_called_once()
        mock_allow.assert_called_once()
        mock_failure.assert_called_once()

    @patch("sentinel_mas.policy_sentinel.secure_executor.get_context")
    @patch("sentinel_mas.policy_sentinel.secure_executor.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.secure_executor.guard")
    @patch("sentinel_mas.policy_sentinel.secure_executor.rbac")
    def test_guard_tool_call_success(
        self, mock_rbac, mock_guard, mock_get_state, mock_get_context
    ) -> None:
        """Test successful guard tool call"""
        # Mock context and state
        mock_context = Mock()
        mock_context.route = "TRACKING"
        mock_context.user_role = "operator"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {"user_question": "Test question"}

        # Mock guard and RBAC to allow
        mock_guard.scan_single.return_value = (True, "clean")
        mock_rbac.is_allowed.return_value = (True, "Allowed")

        # Should not raise
        guard_tool_call(
            tool_name="test_tool", args={"param": "value"}, gate="test_gate"
        )

        mock_guard.scan_single.assert_called_once()
        mock_rbac.is_allowed.assert_called_once_with(
            "operator", "TRACKING", "test_tool"
        )

    @patch("sentinel_mas.policy_sentinel.secure_executor.get_context")
    @patch("sentinel_mas.policy_sentinel.secure_executor.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.secure_executor.guard")
    @patch("sentinel_mas.policy_sentinel.secure_executor.rbac")
    @patch("sentinel_mas.policy_sentinel.secure_executor.guard_deny_and_raise")
    def test_guard_tool_call_injection_deny(
        self, mock_deny, mock_rbac, mock_guard, mock_get_state, mock_get_context
    ) -> None:
        """Test guard tool call with injection detection"""
        # Mock context and state
        mock_context = Mock()
        mock_context.route = "TRACKING"
        mock_context.user_role = "operator"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {"user_question": "Test question"}

        # Mock guard to deny (injection detected)
        mock_guard.scan_single.return_value = (False, "Injection detected")
        # Mock RBAC to allow (so we only test injection denial)
        mock_rbac.is_allowed.return_value = (True, "Allowed")

        guard_tool_call(
            tool_name="test_tool", args={"param": "value"}, gate="test_gate"
        )

        # Should call guard_deny_and_raise exactly once for injection
        mock_deny.assert_called_once_with(
            tool_name="test_tool", reason="Injection detected", gate="test_gate"
        )

    @patch("sentinel_mas.policy_sentinel.secure_executor.get_context")
    @patch("sentinel_mas.policy_sentinel.secure_executor.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.secure_executor.guard")
    @patch("sentinel_mas.policy_sentinel.secure_executor.rbac")
    @patch("sentinel_mas.policy_sentinel.secure_executor.guard_deny_and_raise")
    def test_guard_tool_call_rbac_deny(
        self, mock_deny, mock_rbac, mock_guard, mock_get_state, mock_get_context
    ) -> None:
        """Test guard tool call with RBAC denial"""
        # Mock context and state
        mock_context = Mock()
        mock_context.route = "TRACKING"
        mock_context.user_role = "operator"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {"user_question": "Test question"}

        # Mock guard to allow
        mock_guard.scan_single.return_value = (True, "clean")
        # Mock RBAC to deny
        mock_rbac.is_allowed.return_value = (
            False,
            "Tool 'test_tool' not allowed for role 'operator'",
        )

        guard_tool_call(
            tool_name="test_tool", args={"param": "value"}, gate="test_gate"
        )

        # Should call guard_deny_and_raise exactly once for RBAC denial
        mock_deny.assert_called_once_with(
            tool_name="test_tool",
            reason="Tool 'test_tool' not allowed for role 'operator'",
            gate="test_gate",
        )
