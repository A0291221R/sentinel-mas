from pathlib import Path

import pytest

from sentinel_mas.policy_sentinel.policy.rbac_loader import RBACPolicy


def _write_policy(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "rbac.yml"
    p.write_text(text)
    return p


def test_is_allowed_false_when_role_missing(tmp_path: Path) -> None:
    p = _write_policy(
        tmp_path,
        """
roles:
  operator:
    routes_allowed: [SOP]
    tools_allowed: [search_sop]
""",
    )
    policy = RBACPolicy(p)
    ok, reason = policy.is_allowed("unknown", "SOP", "search_sop")
    assert ok is False
    assert "Unknown role" in reason


def test_route_denied_and_tool_denied(tmp_path: Path) -> None:
    p = _write_policy(
        tmp_path,
        """
roles:
  operator:
    routes_allowed: [SOP]
    tools_allowed: [search_sop]
""",
    )
    policy = RBACPolicy(p)

    ok, reason = policy.is_allowed("operator", "EVENTS", "search_sop")
    assert ok is False and "Route 'EVENTS' not allowed" in reason

    ok, reason = policy.is_allowed("operator", "SOP", "who_entered_zone")
    assert ok is False and "Tool 'who_entered_zone' not allowed" in reason


def test_get_allowed_tools_and_assert_allowed(tmp_path: Path) -> None:
    p = _write_policy(
        tmp_path,
        """
roles:
  analyst:
    routes_allowed: [EVENTS, TRACKING]
    tools_allowed: [list_anomaly_event, send_track]
""",
    )
    policy = RBACPolicy(p)

    # No route filter
    assert set(policy.get_allowed_tools("analyst")) == {
        "list_anomaly_event",
        "send_track",
    }

    # Route filter OK
    assert set(policy.get_allowed_tools("analyst", "EVENTS")) == {
        "list_anomaly_event",
        "send_track",
    }

    # Route not allowed -> empty
    assert policy.get_allowed_tools("analyst", "SOP") == []

    # assert_allowed happy path
    policy.assert_allowed("analyst", "EVENTS", "send_track")

    # assert_allowed should raise on denial
    with pytest.raises(PermissionError):
        policy.assert_allowed("analyst", "SOP", "send_track")


def test_describe_and_get_roles(tmp_path: Path) -> None:
    p = _write_policy(
        tmp_path,
        """
roles:
  viewer:
    routes_allowed: [SOP]
    tools_allowed: []
""",
    )
    policy = RBACPolicy(p)
    assert "viewer" in policy.get_roles()
    msg = policy.describe("viewer")
    assert "Role=viewer" in msg and "Routes=[SOP]" in msg

    # Unknown role path
    assert policy.describe("ghost").startswith("[RBAC] Unknown role:")
