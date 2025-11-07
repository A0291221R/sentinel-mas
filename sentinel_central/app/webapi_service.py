from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc, text
from typing import Any, Dict, Optional

from app.db.db import get_session
from app.db.models import MovementORM, AdEventORM

app = FastAPI()
tracking = APIRouter(prefix="/tracking")
# bus = None  # injected from main.py

# ---------------------------
# Existing endpoint (unchanged)
# ---------------------------
@tracking.get("/insight/{resolved_id}")
async def insight(resolved_id: str) -> Dict[str, Any]:
    async with get_session() as s:
        last_mv = (await s.execute(
            select(MovementORM)
            .where(MovementORM.resolved_id == resolved_id)
            .order_by(desc(MovementORM.ts_ms))
            .limit(1)
        )).scalar_one_or_none()

        last_ad = (await s.execute(
            select(AdEventORM)
            .order_by(desc(AdEventORM.start_ms))
            .limit(1)
        )).scalar_one_or_none()

    return {
        "resolved_id": resolved_id,
        "last_movement": None if not last_mv else {
            "type": last_mv.state,
            "ts_ms": last_mv.ts_ms,
            "camera_id": last_mv.camera_id,
            "location_id": last_mv.location_id
        },
        "last_ad_event": None if not last_ad else {
            "incident": last_ad.incident,
            "confidence": last_ad.confidence,
            "ts_ms": last_ad.start_ms
        }
    }

# ---------------------------
# New: Track / Untrack API
# ---------------------------

# Minimal request body
class TrackCmd(BaseModel):
    resolved_id: str

IDENTITIES_TABLE = "identities"     # change here if your table name differs
IDENTITY_ID_COL = "id"              # change here if your PK column differs


@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/readyz")
def readyz():
    # optionally check DB or other deps here
    return {"ok": True}

# (Optional) read status for UI
@tracking.get("/person/{resolved_id}/tracking")
async def get_tracking_status(resolved_id: str) -> Dict[str, Any]:
    async with get_session() as s:
        row = (await s.execute(
            text(f"SELECT is_tracked FROM {IDENTITIES_TABLE} WHERE {IDENTITY_ID_COL} = :rid")
        , {"rid": resolved_id})).first()
    if not row:
        raise HTTPException(status_code=404, detail="resolved_id not found")
    return {"resolved_id": resolved_id, "is_tracked": bool(row[0])}

@tracking.post("/person/track")
async def track_person(cmd: TrackCmd) -> Dict[str, Any]:
    async with get_session() as s:
        res = (await s.execute(
            text(f"""
                UPDATE {IDENTITIES_TABLE}
                SET is_tracked = TRUE
                WHERE {IDENTITY_ID_COL} = :rid
                RETURNING {IDENTITY_ID_COL}
            """),
            {"rid": cmd.resolved_id}
        )).first()
        if not res:
            raise HTTPException(status_code=404, detail="resolved_id not found")
        await s.commit()

    # If you want to notify other services, publish on your bus here
    # if bus: await bus.publish("tracking.changed", {"resolved_id": cmd.resolved_id, "is_tracked": True})

    return {"status": "ok", "resolved_id": cmd.resolved_id, "is_tracked": True}

@tracking.post("/person/untrack")
async def untrack_person(cmd: TrackCmd) -> Dict[str, Any]:
    async with get_session() as s:
        res = (await s.execute(
            text(f"""
                UPDATE {IDENTITIES_TABLE}
                SET is_tracked = FALSE
                WHERE {IDENTITY_ID_COL} = :rid
                RETURNING {IDENTITY_ID_COL}
            """),
            {"rid": cmd.resolved_id}
        )).first()
        if not res:
            raise HTTPException(status_code=404, detail="resolved_id not found")
        await s.commit()

    # if bus: await bus.publish("tracking.changed", {"resolved_id": cmd.resolved_id, "is_tracked": False})

    return {"status": "ok", "resolved_id": cmd.resolved_id, "is_tracked": False}

# ---------------------------
# Mount router
# ---------------------------
app.include_router(tracking)

