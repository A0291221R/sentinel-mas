import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml
from langchain_core.messages import AIMessage

# Import after adding to path
from sentinel_mas.policy_sentinel.runtime import (
    SentinelContext,
    set_graph_state,
)

# Test database configuration
TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/sentinel_test"

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Global patches to prevent OpenAI initialization
@pytest.fixture(autouse=True)
def global_mock():
    """Mock OpenAI and other external dependencies globally"""
    with (
        patch("langchain_openai.ChatOpenAI") as mock_chat_openai,
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

        yield


@pytest.fixture
def sample_state():
    """Provide a sample state for testing"""
    return {
        "messages": [],
        "user_question": "test question",
        "user_id": "test_user",
        "user_role": "operator",
    }


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    from unittest.mock import Mock

    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="test response")
    return mock_llm


@pytest.fixture(autouse=True)
def mock_all_heavy_imports():
    """Mock ALL heavy imports that cause network calls"""
    with (
        patch("sentence_transformers.SentenceTransformer") as mock_st,
        patch("transformers.AutoConfig.from_pretrained") as mock_config,
        patch("huggingface_hub.file_download.hf_hub_download") as mock_hf_download,
    ):

        # Mock SentenceTransformer
        mock_model = MagicMock()
        mock_st.return_value = mock_model
        mock_model.encode.return_value = [0.1, 0.2, 0.3]  # Mock embedding

        # Mock transformers config
        mock_config.return_value = MagicMock()

        # Mock huggingface downloads
        mock_hf_download.return_value = "/mock/path/model.bin"

        yield


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing - applied before imports"""
    # Clear any existing tracking_tools module to force re-import
    if "sentinel_mas.tools.tracking_tools" in sys.modules:
        del sys.modules["sentinel_mas.tools.tracking_tools"]

    with patch.dict(
        os.environ,
        {
            "SENTINEL_DB_URL": TEST_DB_URL,
            "CENTRAL_URL": "http://test-central:8000",
            "SENTINEL_API_KEY": "test-api-key",
        },
        clear=True,
    ):
        yield


@pytest.fixture
def mock_db_connection():
    """Mock database connection with proper context manager support"""
    with patch("psycopg.connect") as mock_connect:
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Set up the context manager behavior
        mock_connect.return_value = mock_conn
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)

        yield mock_connect, mock_conn, mock_cursor


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for tracking tools"""
    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=None)
        mock_client_instance.request.return_value = mock_response
        yield mock_client, mock_response


@pytest.fixture
def mock_embedding():
    """Mock embedding function"""
    with patch("sentinel_mas.tools.sop_tools.embed_text_unit") as mock_embed:
        mock_embed.return_value = [0.1, 0.2, 0.3]  # Mock embedding vector
        yield mock_embed


# Test Report with JUnit
def pytest_configure(config):
    """Configure pytest hooks for better JUnit reporting"""
    config.option.xmlpath = (
        f"test-results/junit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xml"
    )


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    print(f"\nTest session finished with status: {exitstatus}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add custom properties to JUnit report"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        # Add custom properties to JUnit XML
        report.user_properties.append(("test_module", item.module.__name__))
        report.user_properties.append(("test_function", item.function.__name__))


@pytest.fixture(autouse=True)
def cleanup_context():
    """
    CRITICAL: Clean up context after each test to prevent contamination.
    This runs before and after EVERY test.
    """
    from sentinel_mas.policy_sentinel.runtime import _context_var, _graph_state_var

    # Store original state to restore later
    original_context = _context_var.get()
    original_graph_state = _graph_state_var.get()

    # Reset to clean state BEFORE test runs
    _context_var.set(SentinelContext())
    _graph_state_var.set(None)

    yield  # Run the test

    # Reset to original state AFTER test
    _context_var.set(original_context)
    _graph_state_var.set(original_graph_state)


@pytest.fixture
def mock_runtime_context():
    """Mock runtime context"""
    return SentinelContext(
        user_id="test_user",
        user_role="operator",
        route="TRACKING",
        request_id="test_req_123",
        session_id="test_sess_456",
    )


@pytest.fixture
def sample_graph_state():
    """Sample graph state for testing"""
    return {
        "user_question": "Who entered zone A?",
        "route": "TRACKING",
        "user_id": "test_user",
        "user_role": "operator",
        "request_id": "test_req_123",
        "session_id": "test_sess_456",
        "audit_trail": [],
    }


@pytest.fixture
def with_graph_state(sample_graph_state):
    """Fixture to set graph state for tests that need it"""

    set_graph_state(sample_graph_state)
    return sample_graph_state


@pytest.fixture
def with_runtime_context(mock_runtime_context, with_graph_state):
    """Fixture that sets both context and graph state"""
    from sentinel_mas.policy_sentinel.runtime import _context_var

    _context_var.set(mock_runtime_context)
    return {"context": mock_runtime_context, "state": with_graph_state}


@pytest.fixture
def sample_rbac_policy_file():
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
def sample_injection_policy_file():
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
def sample_redactor_policy_file():
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


# Additional fixtures that might be needed
@pytest.fixture
def mock_tool():
    """Create a mock tool for testing"""
    tool = Mock()
    tool.name = "test_tool"
    tool.invoke = Mock(return_value={"result": "success"})
    return tool


@pytest.fixture
def mock_secure_execute():
    """Mock secure_execute_tool function"""
    with patch(
        "sentinel_mas.policy_sentinel.secure_executor.secure_execute_tool"
    ) as mock:
        yield mock


@pytest.fixture
def mock_guard_tool_call():
    """Mock guard_tool_call function"""
    with patch("sentinel_mas.policy_sentinel.secure_executor.guard_tool_call") as mock:
        yield mock
