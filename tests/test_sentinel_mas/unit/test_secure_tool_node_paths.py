import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from sentinel_mas.policy_sentinel.secure_tool_node import SecureToolNode

pytestmark = pytest.mark.integration


def _ai_with_tools(*tool_specs):
    """
    Build an AIMessage that contains tool_calls = [{id,name,args}, ...]
    """
    return AIMessage(
        content="tools",
        tool_calls=[
            {
                "id": f"tc{i}",
                "name": spec["name"],
                "args": spec.get("args", {}),
                "type": "tool_call",  # optional; keep if your code expects it
            }
            for i, spec in enumerate(tool_specs)
        ],
    )


def test_returns_empty_when_no_messages() -> None:
    node = SecureToolNode(route="SOP", tools=[])
    out = node({"messages": []})
    assert out == {}


def test_returns_empty_when_last_is_not_ai() -> None:
    node = SecureToolNode(route="SOP", tools=[])
    out = node({"messages": ["not an AIMessage"]})
    assert out == {}


def test_unknown_tool_emits_denied_tool_message(monkeypatch) -> None:
    # Empty registry -> unknown tool path
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY", {}, raising=True
    )

    node = SecureToolNode(route="SOP", tools=[])
    ai = _ai_with_tools({"name": "not_registered", "args": {"x": 1}})
    state = {
        "messages": [ai],
        "user_id": "u",
        "user_role": "operator",
        "request_id": "r",
        "session_id": "s",
    }
    out = node(state)
    assert (
        "messages" in out and len(out["messages"]) == 2
    )  # 1 AIMessage + 1 ToolMessage
    tm = out["messages"][-1]
    assert tm.name == "not_registered"
    payload = json.loads(tm.content)
    assert payload["ok"] is False
    assert payload["status"] == "DENIED"
    assert payload["error_type"] == "UnknownTool"


def test_executes_allowed_tool_and_emits_tool_message(monkeypatch) -> None:
    # 1) Make the tool resolvable by the node
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY",
        {"echo": lambda x=1: {"echo": x}},
        raising=True,
    )

    # 2) Bypass RBAC/guards: secure_execute_tool just calls the function
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool",
        lambda tool_name, tool_fn, tool_args: tool_fn(**tool_args),
        raising=True,
    )

    node = SecureToolNode(route="SOP", tools=[])  # tools list is unused by __call__
    ai = _ai_with_tools({"name": "echo", "args": {"x": 7}})

    state = {
        "messages": [ai],  # required by node
        "user_id": "u",  # required by context_scope(...)
        "user_role": "operator",
        "request_id": "r",
        "session_id": "s",
    }

    out = node(state)

    # Expect original AIMessage + one ToolMessage appended
    assert "messages" in out and len(out["messages"]) == 2
    tm = out["messages"][-1]
    assert tm.name == "echo"

    payload = json.loads(tm.content)
    assert payload["ok"] is True
    assert payload["status"] == "OK"
    assert payload["data"] == {"echo": 7}
    assert out.get("halt") is False


def test_permission_error_sets_halt_true(monkeypatch) -> None:
    # Registered tool exists…
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY",
        {"restricted": lambda **k: {"ok": True}},
        raising=True,
    )

    # …but guard denies it via secure_execute_tool
    def deny(tool_name, tool_fn, tool_args):
        raise PermissionError("RBAC denied")

    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool",
        deny,
        raising=True,
    )

    node = SecureToolNode(route="SOP", tools=[])
    ai = _ai_with_tools({"name": "restricted", "args": {}})
    state = {
        "messages": [ai],
        "user_id": "u",
        "user_role": "operator",
        "request_id": "r",
        "session_id": "s",
    }
    out = node(state)
    assert out.get("halt") is True
    tm = out["messages"][-1]
    payload = json.loads(tm.content)
    assert payload["ok"] is False
    assert payload["status"] == "DENIED"
    assert payload["error_type"] == "PermissionError"


def test_value_error_sets_halt_true(monkeypatch) -> None:
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY",
        {"bad": lambda **k: (_ for _ in ()).throw(ValueError("bad param"))},
        raising=True,
    )

    # secure_execute_tool calls the tool_fn and lets ValueError bubble to node
    def call_then_valueerror(tool_name, tool_fn, tool_args):
        return tool_fn(**tool_args)

    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool",
        call_then_valueerror,
        raising=True,
    )

    node = SecureToolNode(route="SOP", tools=[])
    ai = _ai_with_tools({"name": "bad", "args": {"x": 1}})
    state = {
        "messages": [ai],
        "user_id": "u",
        "user_role": "operator",
        "request_id": "r",
        "session_id": "s",
    }
    out = node(state)
    assert out.get("halt") is True
    tm = out["messages"][-1]
    payload = json.loads(tm.content)
    assert payload["status"] == "BAD_REQUEST"
    assert payload["error_type"] == "ValueError"


def test_generic_exception_sets_halt_true(monkeypatch) -> None:
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY",
        {"boom": lambda **k: (_ for _ in ()).throw(RuntimeError("boom"))},
        raising=True,
    )

    def call_then_boom(tool_name, tool_fn, tool_args):
        return tool_fn(**tool_args)

    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool",
        call_then_boom,
        raising=True,
    )

    node = SecureToolNode(route="SOP", tools=[])
    ai = _ai_with_tools({"name": "boom", "args": {}})
    state = {
        "messages": [ai],
        "user_id": "u",
        "user_role": "operator",
        "request_id": "r",
        "session_id": "s",
    }
    out = node(state)
    assert out.get("halt") is True
    payload = json.loads(out["messages"][-1].content)
    assert payload["status"] == "ERROR"
    assert payload["error_type"] == "RuntimeError"


def test_multiple_tool_calls_all_return_messages(monkeypatch) -> None:
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.TOOL_REGISTRY",
        {
            "a": lambda **k: {"ok": "a"},
            "b": lambda **k: {"ok": "b"},
        },
        raising=True,
    )
    monkeypatch.setattr(
        "sentinel_mas.policy_sentinel.secure_tool_node.secure_execute_tool",
        lambda tool_name, tool_fn, tool_args: tool_fn(**tool_args),
        raising=True,
    )

    node = SecureToolNode(route="SOP", tools=[])
    ai = _ai_with_tools({"name": "a"}, {"name": "b"})
    state = {
        "messages": [ai],
        "user_id": "u",
        "user_role": "operator",
        "request_id": "r",
        "session_id": "s",
    }
    out = node(state)
    # 1 AIMessage + 2 ToolMessage
    assert "messages" in out and len(out["messages"]) == 3
    names = [m.name for m in out["messages"]]
    assert names[1:] == ["a", "b"]

    # Parse only the ToolMessages
    tool_msgs = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 2

    payloads: list[Any] = []
    for m in tool_msgs:
        content = m.content
        if isinstance(content, str):
            payloads.append(json.loads(content))
        else:
            # Already structured (list or dict) → use directly
            payloads.append(content)
    assert payloads[-2]["data"] == {"ok": "a"}
    assert payloads[-1]["data"] == {"ok": "b"}
    # Note: current implementation sets halt based on the LAST tool result only
    assert out.get("halt") in (True, False)
