from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RBACPolicy:
    """Lightweight RBAC loader + checker for LLM tool call routing."""

    def __init__(self, policy_path: str | Path):
        path = Path(policy_path)
        if not path.exists():
            raise FileNotFoundError(f"RBAC policy file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self._policy = yaml.safe_load(f)

        self.roles: Dict[str, dict] = self._policy.get("roles", {})
        self.version: str = self._policy.get("version", "unknown")

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def is_allowed(self, user_role: str, route: str, tool_name: str) -> Tuple[bool, str]:
        """
        Check whether a given role may call a tool on a specific route.

        Returns:
            (allowed: bool, reason: str)
        """
        role_cfg = self.roles.get(user_role)
        if not role_cfg:
            return False, f"Unknown role: {user_role}"

        if route not in role_cfg.get("routes_allowed", []):
            return False, f"Route '{route}' not allowed for role '{user_role}'"

        if tool_name not in role_cfg.get("tools_allowed", []):
            return False, f"Tool '{tool_name}' not allowed for role '{user_role}'"

        return True, "Allowed"

    def get_allowed_tools(self, user_role: str, route: Optional[str] = None) -> List[str]:
        """Return all tools allowed for this role (optionally filtered by route)."""
        role_cfg = self.roles.get(user_role)
        if not role_cfg:
            return []

        tools = role_cfg.get("tools_allowed", [])
        if route and route not in role_cfg.get("routes_allowed", []):
            return []
        return tools

    def get_roles(self) -> List[str]:
        """List all known roles."""
        return list(self.roles.keys())

    def describe(self, user_role: str) -> str:
        """Human-readable summary."""
        role_cfg = self.roles.get(user_role)
        if not role_cfg:
            return f"[RBAC] Unknown role: {user_role}"
        routes = ", ".join(role_cfg.get("routes_allowed", []))
        tools = ", ".join(role_cfg.get("tools_allowed", []))
        return f"[RBAC] Role={user_role} | Routes=[{routes}] | Tools=[{tools}]"

    # ------------------------------------------------------------------
    # Optional convenience
    # ------------------------------------------------------------------
    def assert_allowed(self, user_role: str, route: str, tool_name: str) -> None:
        """Raise if not allowed (for enforcement middleware)."""
        ok, reason = self.is_allowed(user_role, route, tool_name)
        if not ok:
            raise PermissionError(reason)


# ----------------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------------
if __name__ == "__main__":
    policy = RBACPolicy("sentinel_mas/policy_sentinel/policy/rbac.yml")

    tests = [
        ("operator", "TRACKING", "send_track"),
        ("analyst", "TRACKING", "send_track"),
        ("analyst", "EVENTS", "list_anomaly_event"),
        ("viewer", "SOP", "who_entered_zone"),
    ]

    for role, route, tool in tests:
        ok, reason = policy.is_allowed(role, route, tool)
        print(f"{role:10s} | {route:10s} | {tool:20s} -> {ok} ({reason})")
