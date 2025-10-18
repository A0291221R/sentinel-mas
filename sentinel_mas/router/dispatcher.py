from __future__ import annotations
from typing import Any, Dict, Optional

from sentinel_mas.tools import TOOL_REGISTRY
from sentinel_mas.gates.input_gate import audit_gate_in
from sentinel_mas.gates.output_gate import audit_gate_out
from sentinel_mas.gates.common import gen_request_id

from sentinel_mas.policy_sentinel.tool_guard import (
    guard_tool_call, audit_tool_result, audit_tool_error
)

def _run_langchain_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """
    Execute a LangChain tool from TOOL_REGISTRY.
    Tries .run(**kwargs) first, then .invoke(kwargs).
    If the tool expects a single string, pass it through.
    """
    tool = TOOL_REGISTRY[tool_name]  # KeyError if missing → good fail-fast
    # Prefer .run if available
    if hasattr(tool, "run"):
        # LangChain @tool sometimes expects a single string; detect that
        if isinstance(args, (str, bytes)):
            return tool.run(args)
        return tool.run(**args)
    # Fallback to .invoke
    if hasattr(tool, "invoke"):
        return tool.invoke(args if not isinstance(args, (str, bytes)) else args)
    raise RuntimeError(f"Tool '{tool_name}' has no supported run/invoke methods")

def invoke_tool(
    route: str,
    role: str,
    tool_name: str,
    args: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Any:
    """
    1) Input Gate  → sanitize/jailbreak check (audits GATE_IN)
    2) Guard       → RBAC + allowlist (audits GUARD_ALLOW/DENY)
    3) Execute     → run the tool
    4) Audit       → TOOL_EXECUTED / TOOL_ERROR
    5) Output Gate → sanitize response (audits GATE_OUT)
    """
    rid = request_id or gen_request_id()

    # 1) Input Gate (sanitize/jailbreak audit)
    safe_ingress = audit_gate_in(
        route, role, args,
        request_id=rid, user_id=user_id, session_id=session_id
    )

    try:
        # 2) Guard (pre-exec audit on allow/deny)
        safe_args = guard_tool_call(
            route, role, tool_name, safe_ingress,
            request_id=rid, user_id=user_id, session_id=session_id
        )

        # 3) Execute the tool
        result = _run_langchain_tool(tool_name, safe_args)

        # 4) Audit success (use sanitized args!)
        audit_tool_result(
            route, role, tool_name, safe_args,
            request_id=rid, user_id=user_id, session_id=session_id
        )

        # 5) Output Gate (always return a sanitized dict)
        payload = result if isinstance(result, dict) else {"result": result}
        return audit_gate_out(
            route, role, payload,
            request_id=rid, user_id=user_id, session_id=session_id
        )

    except Exception as e:
        # Guard already audited GUARD_DENY for PermissionError
        if not isinstance(e, PermissionError):
            # Log runtime/tool errors
            audit_tool_error(
                route, role, tool_name, safe_ingress, e,
                request_id=rid, user_id=user_id, session_id=session_id
            )
            # Optional: also record an egress row with the error body
            try:
                _ = audit_gate_out(
                    route, role, {"error": str(e)},
                    request_id=rid, user_id=user_id, session_id=session_id
                )
            except Exception:
                pass
        raise
