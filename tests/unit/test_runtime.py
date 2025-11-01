import pytest
from sentinel_mas.policy_sentinel.runtime import (
    SentinelContext,
    context_scope,
    get_context,
    get_graph_state,
    graph_state_scope,
)


class TestRuntime:
    def test_sentinel_context_creation(self) -> None:
        """Test SentinelContext creation"""
        context = SentinelContext(
            user_id="test_user",
            user_role="operator",
            route="TRACKING",
            request_id="req123",
            session_id="sess123",
        )

        assert context.user_id == "test_user"
        assert context.user_role == "operator"
        assert context.route == "TRACKING"

    def test_context_scope(self) -> None:
        """Test context scope manager"""
        initial_context = SentinelContext()

        with context_scope(
            user_id="scoped_user",
            user_role="admin",
            request_id="scoped_req",
            session_id="scoped_sess",
            route="SOP",
        ):
            scoped_context = get_context()
            assert scoped_context.user_id == "scoped_user"
            assert scoped_context.user_role == "admin"

        # Should revert to original context
        final_context = get_context()
        assert final_context.user_id == initial_context.user_id

    def test_graph_state_scope(self) -> None:
        """Test graph state scope manager"""
        scoped_state = {"key": "scoped"}

        with graph_state_scope(scoped_state):
            current_state = get_graph_state()
            assert current_state["key"] == "scoped"

        # Should raise after scope ends
        with pytest.raises(RuntimeError):
            get_graph_state()
