from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


# Mock at the crew_agents level where ChatOpenAI is actually used
@pytest.fixture(autouse=True)
def mock_all_dependencies() -> Generator[None, None, None]:
    """Mock all external dependencies before importing crew_agents"""
    with (
        patch("sentinel_mas.agents.crew_agents.ChatOpenAI") as mock_chat_openai,
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
        mock_runtime.system_prompt = "Test system prompt {{ user_question }}"
        mock_runtime.tools = {}
        mock_registry.__getitem__.return_value = mock_runtime

        # Now import your actual classes
        global CrewAgent, State
        from sentinel_mas.agents.crew_agents import CrewAgent, State

        yield


class TestCrewAgents:
    """Unit tests for YOUR actual CrewAgent class"""

    def test_agent_initialization(self) -> None:
        """Test YOUR CrewAgent initialization"""
        # This uses YOUR actual CrewAgent class with mocked dependencies
        agent = CrewAgent("router_agent")

        assert agent.name == "router_agent"
        assert hasattr(agent, "runtime")
        assert hasattr(agent, "llm")

    def test_build_messages(self) -> None:
        """Test YOUR build_messages method"""
        agent = CrewAgent("router_agent")

        test_state = State(
            messages=[HumanMessage(content="How do I handle a fire incident?")],
            user_question="How do I handle a fire incident?",
        )

        # Call YOUR actual method
        messages = agent.build_messages(test_state)

        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert "Test system prompt" in messages[0].content

    def test_agent_call(self) -> None:
        """Test YOUR __call__ method"""
        agent = CrewAgent("router_agent")

        # Mock the LLM response
        mock_response = AIMessage(
            content='{"route": "SOP", "confidence": 0.9, "reason": "SOP question"}'
        )
        agent.llm.invoke.return_value = mock_response

        test_state = State(
            messages=[HumanMessage(content="What's the procedure for X?")],
            user_question="What's the procedure for X?",
        )

        # Call YOUR actual method
        result = agent(test_state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].name == "router_agent"
