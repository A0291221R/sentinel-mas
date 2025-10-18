
from ..policy_sentinel.tool_guard import guard_tool_call

# Expect DENY -> GUARD_DENY row + PermissionError
try:
    guard_tool_call("TRACKING", "operator", "track_person", {"person_id":"A1"}, request_id="demo-1", user_id="u1", session_id="s1")
except PermissionError as e:
    print("DENY OK:", e)

# Expect ALLOW -> GUARD_ALLOW row
guard_tool_call("EVENTS", "operator", "who_entered_zone", {"zone_id":"Z1"}, request_id="demo-2", user_id="u2", session_id="s2")


# SELECT event_type, decision, route, role, tool_name, reason
# FROM audit.tool_invocations
# WHERE request_id IN ('demo-1','demo-2')
# ORDER BY ts;
