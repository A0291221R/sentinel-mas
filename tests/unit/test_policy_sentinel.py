import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest
import yaml
from sentinel_mas.policy_sentinel.runtime import SentinelContext


@pytest.fixture
def sample_rbac_policy_file() -> Generator[str, None, None]:
    """Create a temporary RBAC policy file for testing"""
    policy_content = {
        "version": "1.1",
        "roles": {
            "operator": {
                "routes_allowed": ["SOP", "EVENTS", "TRACKING"],
                "tools_allowed": ["who_entered_zone", "send_track"],
            },
            "viewer": {"routes_allowed": ["SOP"], "tools_allowed": ["search_sop"]},
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(policy_content, f)
        yield f.name

    # Cleanup
    Path(f.name).unlink()


@pytest.fixture
def sample_injection_policy_file() -> Generator[str, None, None]:
    """Create a temporary injection policy file for testing"""
    policy_content = {
        "version": "1.0",
        "block_phrases": [
            "ignore previous instructions",
            "bypass rbac",
            "dump the database",
        ],
        "max_batch_targets": 3,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(policy_content, f)
        yield f.name

    Path(f.name).unlink()


@pytest.fixture
def sample_redactor_policy_file() -> Generator[str, None, None]:
    """Create a temporary redactor policy file for testing"""
    policy_content = {
        "redaction": {
            "max_depth": 3,
            "keys": ["password", "token", "secret", "resolved_id"],
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(policy_content, f)
        yield f.name

    Path(f.name).unlink()


@pytest.fixture
def mock_runtime_context() -> SentinelContext:
    """Mock runtime context for testing"""
    return SentinelContext(
        user_id="test_user",
        user_role="operator",
        route="TRACKING",
        request_id="test_req_123",
        session_id="test_sess_456",
    )


@pytest.fixture
def sample_graph_state() -> dict[str, Any]:
    """Sample graph state for testing"""
    return {
        "user_question": "Who entered zone A?",
        "route": "TRACKING",
        "audit_trail": [],
    }
