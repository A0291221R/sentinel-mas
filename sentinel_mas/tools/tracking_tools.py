from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx
from langchain_core.tools import tool

from sentinel_mas.config import Config

CENTRAL_URL = Config.CENTRAL_URL
SENTINEL_API_KEY = Config.SENTINEL_API_KEY

# from langchain.tools import tool
DEFAULT_TIMEOUT = 5.0
MAX_RETRIES = 2
RETRY_BACKOFF = 0.25


print(
    f"tracking_tools, CENTRAL_URL: {CENTRAL_URL}, SENTINEL_API_KEY:{SENTINEL_API_KEY}"
)


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if SENTINEL_API_KEY:
        h["Authorization"] = f"Bearer {SENTINEL_API_KEY}"
    return h


def _request(
    method: str,
    path: str,
    json: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    url = f"{CENTRAL_URL.rstrip('/')}{path}"
    for attempt in range(MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=timeout, headers=_headers()) as client:
                resp = client.request(method, url, json=json)
                if resp.status_code >= 400:
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except Exception:
                        detail = resp.text
                    return {
                        "ok": False,
                        "status_code": resp.status_code,
                        "error": detail,
                        "endpoint": path,
                    }
                return {
                    "ok": True,
                    "status_code": resp.status_code,
                    "data": resp.json(),
                    "endpoint": path,
                }
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            return {
                "ok": False,
                "status_code": 599,
                "error": f"{type(e).__name__}: {e}",
                "endpoint": path,
            }
    # Fallback for static analyzer — never actually reached
    return {
        "ok": False,
        "status_code": 500,
        "error": "Unexpected error: loop exited without return",
        "endpoint": path,
    }


@tool
def send_track(resolved_id: str) -> Dict[str, Any]:
    """Activate server-side tracking for a person/identity by resolved_id."""
    if not resolved_id:
        return {
            "ok": False,
            "status_code": 400,
            "error": "resolved_id is required",
            "endpoint": "/person/track",
        }
    return _request("POST", "/person/track", json={"resolved_id": resolved_id})


@tool
def send_cancel(resolved_id: str) -> Dict[str, Any]:
    """Cancel/disable server-side tracking for a person/identity by resolved_id."""
    if not resolved_id:
        return {
            "ok": False,
            "status_code": 400,
            "error": "resolved_id is required",
            "endpoint": "/person/untrack",
        }
    return _request("POST", "/person/untrack", json={"resolved_id": resolved_id})


@tool
def get_track_status(resolved_id: str) -> Dict[str, Any]:
    """Fetch current tracking status (is_tracked) for a resolved_id."""
    if not resolved_id:
        return {
            "ok": False,
            "status_code": 400,
            "error": "resolved_id is required",
            "endpoint": "/person/{id}/tracking",
        }
    return _request("GET", f"/person/{resolved_id}/tracking")


@tool
def get_person_insight(resolved_id: str) -> Dict[str, Any]:
    """Get last movement and last ad event for a resolved_id (context only)."""
    if not resolved_id:
        return {
            "ok": False,
            "status_code": 400,
            "error": "resolved_id is required",
            "endpoint": "/insight/{id}",
        }
    return _request("GET", f"/insight/{resolved_id}")
