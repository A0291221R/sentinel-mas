# sentinel_mas/gates/common.py
from __future__ import annotations
import os
import re
import json
import time
from typing import Any, Dict
from sentinel_mas.policy_sentinel.policy import DISALLOWED_ATTR_KEYS, JAILBREAK_PATTERNS

# Secret keys to mask
_SECRET_KEYS = {"api_key","apikey","token","auth","password","secret","authorization","bearer","key"}

# Precompile jailbreak patterns
_JAILBREAK_RE = re.compile("|".join(JAILBREAK_PATTERNS), flags=re.IGNORECASE)

def now_ms() -> int:
    return int(time.time() * 1000)

def gen_request_id() -> str:
    return f"req_{now_ms()}_{os.getpid()}"

def mask(value: Any) -> Any:
    if isinstance(value, str):
        return (value[:4] + "..." + value[-2:]) if len(value) > 8 else "***"
    if isinstance(value, (bytes, bytearray)):
        return f"<{type(value).__name__}:{len(value)} bytes>"
    return "***"

def sanitize_payload(payload: Dict[str, Any], max_len: int = 10_000) -> Dict[str, Any]:
    """Remove secrets, large values, disallowed attribute keys."""
    def scrub(k: str, v: Any) -> Any:
        lk = k.lower()
        if any(s in lk for s in _SECRET_KEYS):
            return mask(v)
        if lk in DISALLOWED_ATTR_KEYS:
            return "<redacted-by-policy>"
        if isinstance(v, (bytes, bytearray)):
            return f"<{type(v).__name__}:{len(v)} bytes>"
        if isinstance(v, str) and len(v) > 512:
            return v[:512] + f"... (truncated {len(v)-512} chars)"
        if isinstance(v, (list, tuple)) and len(v) > 64:
            return list(v[:64]) + [f"... (+{len(v)-64} more)"]
        if isinstance(v, dict):
            return {ik: scrub(ik, iv) for ik, iv in v.items()}
        return v

    safe = {k: scrub(k, v) for k, v in (payload or {}).items()}
    s = json.dumps(safe, ensure_ascii=False)
    if len(s) > max_len:
        return {"_truncated": True, "preview": s[:max_len] + f"... (truncated {len(s)-max_len} chars)"}
    return safe

def contains_jailbreak(payload: Dict[str, Any]) -> bool:
    """Check common text fields for jailbreak patterns."""
    for key in ("prompt","message","content","query","text","instruction"):
        val = payload.get(key)
        if isinstance(val, str) and _JAILBREAK_RE.search(val):
            return True
    return False
