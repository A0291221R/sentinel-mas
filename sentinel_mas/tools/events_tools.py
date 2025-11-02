from __future__ import annotations

from typing import Any, Dict, List, Optional

import psycopg
from langchain_core.tools import tool

from sentinel_mas.config import Config

DSN = Config.SENTINEL_DB_URL
# print(f"event_tools, DSN: {DSN}")


def _rows(cursor: Any) -> List[dict]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in cursor.fetchall()]


def _clamp_limit(x: Optional[int | str], default: int = 50, max_cap: int = 1000) -> int:
    try:
        v = int(x or default)
    except Exception:
        v = default
    return max(1, min(v, max_cap))


# class WhoEnteredArgs(BaseModel):
#     location_id: str = Field(..., description="Location
#       (person_sessions.location_id)")
#     start_ms: int = Field(..., description="Start time in epoch ms")
#     end_ms: int = Field(..., description="End time in epoch ms")
#     camera_id: Optional[str] = Field(None, description="Optional camera filter")
#     limit: int = Field(50, description="Max rows (1–1000)")


# @tool(args_schema=WhoEnteredArgs)
@tool
def who_entered_zone(
    location_id: str,
    start_ms: int,
    end_ms: int,
    camera_id: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """List persons (from person_sessions) who appeared within a time window.
    Filters: location_id (required), camera_id (optional).
    Returns: track_id, resolved_id, location_id, appear_ms, disappear_ms, cam_id.
    """
    limit = _clamp_limit(limit, default=50, max_cap=1000)
    sql = """
        SELECT
            track_id,
            resolved_id,
            location_id,
            appear_ms,
            disappear_ms,
            camera_id AS cam_id,
            to_char((to_timestamp(appear_ms/1000.0) AT TIME ZONE 'Asia/Singapore'),
                    'YYYY-MM-DD HH24:MI:SS') AS appear_at_sgt
        FROM person_sessions
        WHERE location_id = %s
          AND appear_ms BETWEEN %s AND %s
          AND (camera_id = COALESCE(%s::text, camera_id))
        ORDER BY appear_ms ASC
        LIMIT %s;
    """
    params = (location_id, start_ms, end_ms, camera_id, limit)
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = _rows(cur)
    return {
        "ok": True,
        "filters": {
            "location_id": location_id,
            "camera_id": camera_id,
            "start_ms": start_ms,
            "end_ms": end_ms,
        },
        "rows": rows,
        "count": len(rows),
        "limit": limit,
        "source": "person_sessions",
    }


@tool
def list_anomaly_event(
    start_ms: int,
    end_ms: int,
    location_id: Optional[str] = None,
    camera_id: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """List anomaly/incident episodes from public.ad_events in a time window.
    Optional filters: location_id, camera_id. Returns ts_ms=start_ms,
    location_id, cam_id, incident, phase, confidence, episode,
    ad_event_id, end_ms, duration_ms.
    """
    limit = _clamp_limit(limit, default=100, max_cap=1000)
    sql = """
        SELECT
            start_ms                AS ts_ms,
            location_id,
            camera_id               AS cam_id,
            incident,
            phase,
            confidence,
            episode,
            id                      AS ad_event_id,
            end_ms,
            duration_ms,
            to_char((to_timestamp(start_ms/1000.0) AT TIME ZONE 'Asia/Singapore'),
                    'YYYY-MM-DD HH24:MI:SS') AS ts_at_sgt
        FROM public.ad_events
        WHERE start_ms BETWEEN %s AND %s
            AND location_id = COALESCE(%s::text, location_id)
            AND camera_id  = COALESCE(%s::text,  camera_id)
        ORDER BY start_ms ASC
        LIMIT %s;
    """
    params = (start_ms, end_ms, location_id, camera_id, limit)
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = _rows(cur)
    return {
        "ok": True,
        "filters": {
            "start_ms": start_ms,
            "end_ms": end_ms,
            "location_id": location_id,
            "camera_id": camera_id,
        },
        "rows": rows,
        "count": len(rows),
        "limit": limit,
        "source": "public.ad_events",
    }
