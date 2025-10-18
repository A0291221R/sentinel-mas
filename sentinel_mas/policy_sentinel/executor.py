# sentinel_mas/policy_sentinel/executor.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json, time, inspect
from langchain_core.messages import AIMessage, ToolMessage

# Context and guard live under policy_sentinel
from .runtime import set_context_from_state, get_context
from .tool_guard import guard_tool_call, audit_tool_result, audit_tool_error

# Gates live under sentinel_mas/gates (absolute import because we're inside policy_sentinel)
from sentinel_mas.gates.input_gate import audit_gate_in
from sentinel_mas.gates.output_gate import audit_gate_out
from sentinel_mas.gates.common import gen_request_id


class PolicyExecutor:
    """
    Intercepts tool_calls from the last AIMessage, enforces policy,
    optionally freezes time window, executes the tool(s), and audits.

    Usage:
      events_exec = PolicyExecutor(
          route="EVENTS",
          tools=[who_entered_zone, list_anomaly_event],
          freeze_time_window=True,   # force start_ms/end_ms from state if available
          single_call=True           # only execute first tool_call
      )
    """
    def __init__(
        self,
        route: str,                           # "SOP" | "EVENTS" | "TRACKING"
        tools: List[Any],
        *,
        agent_name: Optional[str] = None,
        single_call: bool = True,
        freeze_time_window: bool = False,
        override_keys: Optional[List[str]] = None,  # extra keys to freeze from state (e.g., ["location_id"])
        route_from_state: bool = False,       # if True, use state["route"] or state["router_decision"]["route"]
    ):
        self.route = route
        self.agent_name = agent_name or f"{route.lower()}_agent"
        self.single_call = single_call
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

    # ---- helpers ----
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

    def _state_overrides(self, args: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # Always coerce ints for ms if present in state
        if self.freeze_time_window and ("start_ms" in state and "end_ms" in state):
            if "start_ms" in args: args["start_ms"] = int(state["start_ms"])
            if "end_ms"   in args: args["end_ms"]   = int(state["end_ms"])
        # Any extra override keys you want to force from state (e.g., location_id)
        for k in self.override_keys:
            if k in state and k in args:
                args[k] = state[k]
        return args

    def _exec_one(
        self,
        *,
        route: str,
        tool_name: str,
        raw_args: Dict[str, Any],
        tool_call_id: str,
        state: Dict[str, Any],
    ) -> ToolMessage:
        # Bind context (user_id, user_role, route, request/session ids)
        set_context_from_state({**state, "route": route})
        ctx = get_context()
        role = ctx["user_role"]
        user = ctx["user_id"]
        session_id = state.get("session_id")
        rid = state.get("request_id") or gen_request_id()

        # Merge/override args from state if configured (these are the args we actually intend to run)
        args = self._state_overrides(dict(raw_args or {}), state)

        # 1) Input gate — sanitize + early jailbreak block + audit GATE_IN
        try:
            ingress_args = audit_gate_in(
                route, role, args,
                request_id=rid, user_id=user, session_id=session_id
            )
        except PermissionError as e:
            # Return an audited error payload as a ToolMessage
            err_payload = {"ok": False, "error": str(e)}
            return ToolMessage(
                content=json.dumps(err_payload, ensure_ascii=False),
                tool_call_id=tool_call_id or "tool_call_0",
                name=tool_name,
            )

        # 2) Policy guard (RBAC + allowlist; audits GUARD_ALLOW/DENY)
        try:
            safe_args = guard_tool_call(
                route, role, tool_name, ingress_args,
                request_id=rid, user_id=user, session_id=session_id
            )
        except PermissionError as e:
            # GUARD_DENY already audited inside guard; surface a clean error ToolMessage
            err_payload = {"ok": False, "error": str(e)}
            return ToolMessage(
                content=json.dumps(err_payload, ensure_ascii=False),
                tool_call_id=tool_call_id or "tool_call_0",
                name=tool_name,
            )

        # 3) Execute the tool
        t0 = time.time()
        err: Optional[str] = None
        rows_count: Optional[int] = None
        tool = self.tools.get(tool_name)
        if tool is None:
            err = f"Unknown tool '{tool_name}'"
            result: Dict[str, Any] = {"ok": False, "error": err}
            latency = int((time.time() - t0) * 1000)
        else:
            try:
                # LangChain Tool has .invoke; plain callables don't
                if hasattr(tool, "invoke"):
                    result = tool.invoke(safe_args)
                else:
                    # Be resilient: support either kwargs or a single dict param
                    sig = inspect.signature(tool)
                    if len(sig.parameters) == 1 and next(iter(sig.parameters.values())).annotation in (dict, Dict[str, Any]):
                        result = tool(safe_args)
                    else:
                        result = tool(**safe_args)
                latency = int((time.time() - t0) * 1000)

                # Try to capture row count for audit (not persisted here; left for metrics if you add later)
                if isinstance(result, dict) and isinstance(result.get("rows"), list):
                    rows_count = len(result["rows"])
            except Exception as e:
                latency = int((time.time() - t0) * 1000)
                err = f"{type(e).__name__}: {e}"
                result = {"ok": False, "error": err}

        # 4) Audit tool outcome (TOOL_EXECUTED / TOOL_ERROR)
        try:
            if err is None:
                audit_tool_result(
                    route, role, tool_name, safe_args,
                    request_id=rid, user_id=user, session_id=session_id
                )
            else:
                audit_tool_error(
                    route, role, tool_name,
                    safe_args if 'safe_args' in locals() else ingress_args,
                    Exception(err),
                    request_id=rid, user_id=user, session_id=session_id
                )
        except Exception:
            # never let audit failures break the flow
            pass

        # 5) Output gate — sanitize response & audit GATE_OUT
        try:
            payload = result if isinstance(result, dict) else {"result": result}
            egress = audit_gate_out(
                route, role, payload,
                request_id=rid, user_id=user, session_id=session_id
            )
        except Exception:
            # If output-gate fails (shouldn’t), fall back to raw result
            egress = result if isinstance(result, dict) else {"result": result}

        return ToolMessage(
            content=json.dumps(egress, ensure_ascii=False),
            tool_call_id=tool_call_id or "tool_call_0",
            name=tool_name,
        )

    # ---- LangGraph node entry ----
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        ai = self._last_ai(messages)
        if not ai or not getattr(ai, "tool_calls", None):
            return {}

        tool_messages: List[ToolMessage] = []

        # FIX: openai requires response to every tool_call_id to satisfy the API.
        # calls = ai.tool_calls[:1] if self.single_call else ai.tool_calls
        calls = ai.tool_calls 
        route = self._get_route(state)

        for tc in calls:
            name = tc.get("name")
            args = tc.get("args") or {}
            tcid = tc.get("id") or tc.get("tool_call_id") or "tool_call_0"
            tm = self._exec_one(route=route, tool_name=name, raw_args=args, tool_call_id=tcid, state=state)
            tool_messages.append(tm)

        return {"messages": tool_messages}
