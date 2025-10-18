from typing import Literal, Dict, List

Role  = Literal["viewer","operator","supervisor","admin"]
Route = Literal["SOP","EVENTS","TRACKING"]

ROUTE_RBAC: Dict[Role, List[Route]] = {
    "viewer":     ["SOP"],
    "operator":   ["SOP","EVENTS"],
    "supervisor": ["SOP","EVENTS","TRACKING"],
    "admin":      ["SOP","EVENTS","TRACKING"],
}

TOOLS_ALLOWLIST: Dict[Route, List[str]] = {
    "SOP":     ["search_sop","get_sop"],
    "EVENTS":  ["who_entered_zone","list_anomaly_event"],
    "TRACKING":["send_track", "send_cancel", "get_track_status"],
}

DISALLOWED_ATTR_KEYS = {"race","ethnicity","religion","gender_identity","politics"}

JAILBREAK_PATTERNS = [
    r"ignore previous instructions", r"you are now", r"system prompt",
    r"bypass safety", r"unfiltered model", r"as an unfiltered model",
]
