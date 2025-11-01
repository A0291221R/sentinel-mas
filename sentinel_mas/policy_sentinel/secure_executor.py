import time
from typing import Any, Dict

from sentinel_mas.policy_sentinel.audit import (
    audit_guard_allow,
    audit_tool_failure,
    audit_tool_success,
    guard_deny_and_raise,
)
from sentinel_mas.policy_sentinel.policy import guard, rbac
from sentinel_mas.policy_sentinel.runtime import get_context, get_graph_state


def _now_ms() -> int:
    return int(time.time() * 1000)


def _safe_preview(result: Any) -> Any:
    # Keep this tiny. DON'T dump full DB rows or PII.
    # Just return a high-level status dict.
    if isinstance(result, dict):
        preview = {
            k: v
            for k, v in result.items()
            if k in ("ok", "status_code", "msg", "count", "id")
        }
        return preview
    return {"type": type(result).__name__}


def call_tool_safely(tool_obj: Any, tool_args: Dict[str, Any]) -> Any:
    """
    Execute a tool object safely regardless of whether it's a LangChain
    StructuredTool, BaseTool, or plain Python callable.

    Supported patterns:
    - StructuredTool / BaseTool: uses .invoke() or .run()
    - Plain function / callable class: calls directly

    Returns:
        The raw result (not wrapped). Caller should handle audit and message wrapping.

    Raises:
        TypeError if the object has no valid call interface.
    """
    # LangChain StructuredTool / Runnable protocol
    if hasattr(tool_obj, "invoke") and callable(getattr(tool_obj, "invoke")):
        return tool_obj.invoke(tool_args)

    # Legacy Tool API
    if hasattr(tool_obj, "run") and callable(getattr(tool_obj, "run")):
        return tool_obj.run(tool_args)

    # Plain callable
    if callable(tool_obj):
        return tool_obj(**tool_args)

    raise TypeError(f"Unsupported tool type: {type(tool_obj).__name__}")


def guard_tool_call(tool_name: str, args: Dict[str, Any], gate: str) -> None:
    """
    Enforce route/role policy and ALWAYS audit the decision.
    On DENY: writes a 'DENY' record, then raises PermissionError.
    On ALLOW: returns sanitized args (so caller uses safe args).
    """
    ctx = get_context()
    state = get_graph_state()

    # print(f"\n[guard_tool_call] state: {state}\n")
    route = ctx.route if ctx.route else ""
    role = ctx.user_role
    user_question = state.get("user_question", "")

    # Prompt injection / jailbreak screen
    allowed, reason = guard.scan_single(
        user_msg=user_question, tool_name=tool_name, tool_args=args
    )
    if not allowed:
        guard_deny_and_raise(tool_name=tool_name, reason=reason, gate=gate)

    # RBAC authorization check
    allowed, reason = rbac.is_allowed(role, route, tool_name)
    if not allowed:
        guard_deny_and_raise(tool_name=tool_name, reason=reason, gate=gate)


def secure_execute_tool(tool_name: str, tool_fn: Any, tool_args: dict) -> Any:
    # 1. Guard + pre-audit
    guard_tool_call(
        tool_name=tool_name,
        args=tool_args,
        gate="tool_gate",
    )

    # 2. Audit that guards passed
    audit_guard_allow(
        tool_name=tool_name, detail="RBAC, route, and injection checks passed"
    )

    # 3. Execute tool
    try:
        result = call_tool_safely(tool_fn, tool_args)
        audit_tool_success(
            tool_name=tool_name,
            raw_args=tool_args,
            result_preview=_safe_preview(result),
        )
        return result
    except Exception as exc:
        audit_tool_failure(
            tool_name=tool_name,
            raw_args=tool_args,
            exc=exc,
        )
        raise
