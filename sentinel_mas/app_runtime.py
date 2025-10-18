# sentinel_mas/app_runtime.py
from __future__ import annotations
import os
import importlib
from typing import Iterable, Dict

# Modules that define your @tool functions so LangChain registers them.
_TOOL_MODULES: Iterable[str] = (
    "sentinel_mas.tools.sop_tools",
    "sentinel_mas.tools.events_tools",
    "sentinel_mas.tools.tracking_tools",
    # add more modules here as you create them
)

def _import_modules(mod_paths: Iterable[str]) -> None:
    for m in mod_paths:
        try:
            importlib.import_module(m)
        except Exception as e:
            # fail-soft so one bad tool doesn't prevent boot
            print(f"[app_runtime] WARN: failed to import {m}: {e}")

def validate_tool_allowlist() -> None:
    """Ensure every allowlisted tool in policy.py is actually registered."""
    from sentinel_mas.tools import TOOL_REGISTRY
    from sentinel_mas.policy_sentinel.policy import TOOLS_ALLOWLIST
    missing: Dict[str, list[str]] = {}
    for route, tools in TOOLS_ALLOWLIST.items():
        for t in tools:
            if t not in TOOL_REGISTRY:
                missing.setdefault(route, []).append(t)
    if missing:
        pretty = ", ".join(f"{r}=[{', '.join(ts)}]" for r, ts in missing.items())
        raise RuntimeError(f"[app_runtime] Tools in allowlist not registered: {pretty}")

def start_runtime(*, with_metrics: bool = False) -> None:
    """
    Call once at service startup (API app startup, worker boot, etc.).
    Loads tools and validates policy. Metrics are optional.
    """
    _import_modules(_TOOL_MODULES)

    # After decorators run, the registry is populated.
    from sentinel_mas.tools import TOOL_REGISTRY
    print(f"[app_runtime] TOOL_REGISTRY loaded: {len(TOOL_REGISTRY)} tools")

    validate_tool_allowlist()
    print("[app_runtime] policy allowlist validated")

    # Optional Prometheus (safe to skip if not installed)
    if with_metrics and os.getenv("PROMETHEUS_PORT"):
        try:
            from prometheus_client import start_http_server
            port = int(os.getenv("PROMETHEUS_PORT", "9100"))
            start_http_server(port)
            print(f"[app_runtime] metrics exporter up on :{port}/metrics")
        except Exception as e:
            print(f"[app_runtime] WARN: metrics not started: {e}")

    print("[startup] registered tools:", sorted(TOOL_REGISTRY.keys()))
