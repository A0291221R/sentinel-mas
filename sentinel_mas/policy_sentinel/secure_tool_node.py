# sentinel_mas/policy_sentinel/executor.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, ToolMessage

from sentinel_mas.policy_sentinel.runtime import (
    context_scope,
    graph_state_scope,
)
from sentinel_mas.policy_sentinel.secure_executor import secure_execute_tool
from sentinel_mas.tools import TOOL_REGISTRY


class SecureToolNode:
    """
    Intercepts tool_calls from the last AIMessage, enforces policy,
    optionally freezes time window, executes the tool(s), and audits.

    Usage:
      events_exec = SecureToolNode(
          route="EVENTS",
          tools=[who_entered_zone, list_anomaly_event],
          freeze_time_window=True,   # force start_ms/end_ms from state if available
      )
    """

    def __init__(
        self,
        route: str,  # "SOP" | "EVENTS" | "TRACKING"
        tools: List[Any],
        *,
        agent_name: Optional[str] = None,
        freeze_time_window: bool = False,
        override_keys: Optional[
            List[str]
        ] = None,  # extra keys to freeze from state (e.g., ["location_id"])
        # if True, use state["route"] or state["router_decision"]["route"]
        route_from_state: bool = False,
    ):
        self.route = route
        self.agent_name = agent_name or f"{route.lower()}_agent"
        self.freeze_time_window = freeze_time_window
        self.override_keys = set(override_keys or [])
        self.route_from_state = route_from_state

        # Build name->callable map
        self.tools: Dict[str, Any] = {}
        for t in tools:
            name = getattr(t, "name", None) or getattr(t, "__name__", None)
            if not name:
                raise ValueError("Tool must have .name or __name__")
            self.tools[name] = t

    def _get_route(self, state: Dict[str, Any]) -> str:
        if self.route_from_state:
            r = state.get("route")
            if not r and isinstance(state.get("router_decision"), dict):
                r = state["router_decision"].get("route")
            return r or self.route
        return self.route

    def _last_ai(self, messages: List[Any]) -> Optional[AIMessage]:
        for m in reversed(messages or []):
            if isinstance(m, AIMessage):
                return m
        return None

    def _state_overrides(
        self, args: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Always coerce ints for ms if present in state
        if self.freeze_time_window and ("start_ms" in state and "end_ms" in state):
            if "start_ms" in args:
                args["start_ms"] = int(state["start_ms"])
            if "end_ms" in args:
                args["end_ms"] = int(state["end_ms"])
        # Any extra override keys you want to force from state (e.g., location_id)
        for k in self.override_keys:
            if k in state and k in args:
                args[k] = state[k]
        return args

    # ---- LangGraph node entry ----
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        ai = self._last_ai(messages)
        if not ai or not getattr(ai, "tool_calls", None):
            return {}

        # print(f'\n[SecureToolNode {self.agent_name}], state: {state}\n')
        tool_calls = ai.tool_calls
        tool_messages: List[ToolMessage] = []

        with (
            context_scope(
                user_id=state["user_id"],
                user_role=state["user_role"],
                request_id=state["request_id"],
                session_id=state["session_id"],
                route=self._get_route(state),
            ),
            graph_state_scope(state),
        ):
            is_halt = False
            for tc in tool_calls:
                name = tc.get("name", "")
                args = tc.get("args") or {}
                # args = self._state_overrides(dict(args or {}), state)
                tcid = tc.get("id") or tc.get("tool_call_id") or "tool_call_0"

                fn = TOOL_REGISTRY.get(name)

                # if LLM hallucinated a tool we don't even have
                if fn is None:
                    error_payload = {
                        "ok": False,
                        "status": "DENIED",
                        "error_type": "UnknownTool",
                        "msg": f"Tool '{name}' is not registered or not allowed.",
                    }
                    tool_messages.append(
                        ToolMessage(
                            content=json.dumps(error_payload, ensure_ascii=False),
                            tool_call_id=tcid,
                            name=name,
                        )
                    )
                    continue

                # normal case: execute tool with guardrails
                try:
                    result = secure_execute_tool(
                        tool_name=name,
                        tool_fn=fn,
                        tool_args=args,
                    )

                    # you can standardize success format if you want
                    payload = {
                        "ok": True,
                        "status": "OK",
                        "data": result,
                    }
                    is_halt = False

                except PermissionError as e:
                    # RBAC / policy_sentinel said NO
                    payload = {
                        "ok": False,
                        "status": "DENIED",
                        "error_type": "PermissionError",
                        "msg": str(e) or "You are not allowed to perform this action.",
                    }
                    is_halt = True

                except ValueError as e:
                    # bad / missing params etc.
                    payload = {
                        "ok": False,
                        "status": "BAD_REQUEST",
                        "error_type": "ValueError",
                        "msg": str(e),
                    }
                    is_halt = True

                except Exception as e:
                    # unexpected tool failure
                    payload = {
                        "ok": False,
                        "status": "ERROR",
                        "error_type": e.__class__.__name__,
                        "msg": str(e),
                    }
                    is_halt = True

                # always push a ToolMessage back to the model
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(payload, ensure_ascii=False),
                        tool_call_id=tcid,
                        name=name,
                    )
                )

        new_state = {
            **state,
            "messages": state.get("messages", []) + tool_messages,
            "halt": is_halt,
        }

        # print("[SecureToolNode RETURN]", new_state.keys(), "halt=", new_state["halt"])
        return new_state
