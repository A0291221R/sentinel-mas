from unittest.mock import MagicMock, Mock, patch

import pytest

from sentinel_mas.policy_sentinel.audit import (
    audit_guard_allow,
    audit_tool_failure,
    audit_tool_success,
    guard_deny_and_raise,
)


class TestAuditSystem:

    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_context")
    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.audit.record_audit")
    def test_guard_deny_and_raise(
        self,
        mock_record_audit: MagicMock,
        mock_get_state: MagicMock,
        mock_get_context: MagicMock,
    ) -> None:
        """Test guard deny raises PermissionError and audits"""
        # Mock context and state
        mock_context = Mock()
        mock_context.request_id = "test_req"
        mock_context.user_id = "test_user"
        mock_context.user_role = "operator"
        mock_context.route = "TRACKING"
        mock_context.session_id = "test_sess"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {
            "user_question": "Test question",
            "route": "TRACKING",
        }

        with pytest.raises(PermissionError):
            guard_deny_and_raise(
                tool_name="test_tool", reason="Test denial", gate="TEST_GATE"
            )

        mock_record_audit.assert_called_once()

    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_context")
    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.audit.record_audit")
    def test_audit_guard_allow(
        self,
        mock_record_audit: MagicMock,
        mock_get_state: MagicMock,
        mock_get_context: MagicMock,
    ) -> None:
        """Test guard allow audit"""
        # Mock context and state
        mock_context = Mock()
        mock_context.request_id = "test_req"
        mock_context.user_id = "test_user"
        mock_context.user_role = "operator"
        mock_context.route = "TRACKING"
        mock_context.session_id = "test_sess"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {
            "user_question": "Test question",
            "route": "TRACKING",
        }

        audit_guard_allow(tool_name="test_tool", detail="Test allow")

        mock_record_audit.assert_called_once()

    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_context")
    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.audit.record_audit")
    def test_audit_tool_success(
        self,
        mock_record_audit: MagicMock,
        mock_get_state: MagicMock,
        mock_get_context: MagicMock,
    ) -> None:
        """Test tool success audit"""
        # Mock context and state
        mock_context = Mock()
        mock_context.request_id = "test_req"
        mock_context.user_id = "test_user"
        mock_context.user_role = "operator"
        mock_context.route = "TRACKING"
        mock_context.session_id = "test_sess"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {
            "user_question": "Test question",
            "route": "TRACKING",
        }

        audit_tool_success(
            tool_name="test_tool",
            raw_args={"param": "value"},
            result_preview={"status": "OK"},
        )

        mock_record_audit.assert_called_once()

    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_context")
    @patch("sentinel_mas.policy_sentinel.audit.runtime.get_graph_state")
    @patch("sentinel_mas.policy_sentinel.audit.record_audit")
    def test_audit_tool_failure(
        self,
        mock_record_audit: MagicMock,
        mock_get_state: MagicMock,
        mock_get_context: MagicMock,
    ) -> None:
        """Test tool failure audit"""
        # Mock context and state
        mock_context = Mock()
        mock_context.request_id = "test_req"
        mock_context.user_id = "test_user"
        mock_context.user_role = "operator"
        mock_context.route = "TRACKING"
        mock_context.session_id = "test_sess"
        mock_get_context.return_value = mock_context

        mock_get_state.return_value = {
            "user_question": "Test question",
            "route": "TRACKING",
        }

        test_exception = ValueError("Test error")

        audit_tool_failure(
            tool_name="test_tool", raw_args={"param": "value"}, exc=test_exception
        )

        mock_record_audit.assert_called_once()
