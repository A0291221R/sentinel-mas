from types import SimpleNamespace
from typing import Any, Generator

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def patch_chat_openai(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Prevent LangChain from instantiating real OpenAI clients during import."""

    class DummyLLM:
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

        def invoke(self, *a: Any, **kw: Any) -> SimpleNamespace:
            return SimpleNamespace(content="ok")

    # Patch both common import paths
    monkeypatch.setattr(
        "sentinel_mas.agents.crew_agents.ChatOpenAI", DummyLLM, raising=False
    )
    monkeypatch.setattr(
        "sentinel_mas.agents.crew_with_guard.ChatOpenAI", DummyLLM, raising=False
    )
    monkeypatch.setattr("langchain_openai.ChatOpenAI", DummyLLM, raising=False)

    # Also neutralize any global model config used by the agents
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    yield
