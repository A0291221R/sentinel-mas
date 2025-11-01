import builtins
import importlib
import io
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
    monkeypatch.setattr("sentinel_mas.agents.crew.ChatOpenAI", DummyLLM, raising=False)
    monkeypatch.setattr("langchain_openai.ChatOpenAI", DummyLLM, raising=False)

    # Also neutralize any global model config used by the agents
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    yield


def test_app_with_guard_import_smoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    # Fake CreateCrew().get_graph().draw_mermaid_png()
    fake_graph = SimpleNamespace(draw_mermaid_png=lambda: b"PNG")
    fake_app = SimpleNamespace(get_graph=lambda: fake_graph)

    # crew_with_guard.CreateCrew is used by app_with_guard.py
    monkeypatch.setattr(
        "sentinel_mas.agents.crew_with_guard.CreateCrew",
        lambda: fake_app,
        raising=True,
    )

    # If the module writes "sentinel_flow.png" at import, redirect open() to tmp file
    out_file = tmp_path / "sentinel_flow.png"

    _open = builtins.open

    def fake_open(path: str, mode: str = "r", *a: Any, **kw: Any) -> Any:
        # Allow text reads; redirect binary write to tmp path
        if "wb" in mode:
            path = out_file
        return _open(path, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", fake_open, raising=True)

    m = importlib.import_module("sentinel_mas.app.app_with_guard")
    assert m is not None
    # if write happened, file exists; if not, import still succeeded
    # both are acceptable for smoke
    if out_file.exists():
        assert out_file.read_bytes() == b"PNG"


def test_app_import_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    # Some repos still import a legacy crew.CreateCrew in app.py; give it a stub
    fake_app = SimpleNamespace(
        get_graph=lambda: SimpleNamespace(draw_mermaid_png=lambda: b"")
    )
    monkeypatch.setattr(
        "sentinel_mas.agents.crew.CreateCrew",
        lambda: fake_app,
        raising=False,  # tolerate if module isn't used
    )
    m = importlib.import_module("sentinel_mas.app.app")
    assert hasattr(m, "app")
