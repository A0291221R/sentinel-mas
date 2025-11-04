import json
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.utils import to_pgvector_literal
from app.db.models import PersonSessionORM
import time, uuid



def _new_session_id(ts_ms: int) -> str:
    return f"s_{ts_ms}_{uuid.uuid4().hex[:6]}"

async def open_or_update_session_on_move_in(
    s: AsyncSession,
    resolved_id: str,
    location_id: str | None,
    camera_id: str | None,
    ts_ms: int,
    rep_image: str | None,
    rep_attrs: dict | list | None,
    rep_attr_names: list[str] | None,
    rep_scores: list[float] | None,
    rep_embedding: list[float] | None,
    track_id: str | None,
) -> None:
    # if there is an active session (no disappear_ms) for same resolved_id+location+camera, don’t create a duplicate
    row = (await s.execute(
        text("""
            SELECT session_id FROM person_sessions
            WHERE track_id = :tid
              AND COALESCE(location_id,'') = COALESCE(:loc,'')
              AND COALESCE(camera_id,'') = COALESCE(:cam,'')
              AND disappear_ms IS NULL
            ORDER BY appear_ms DESC
            LIMIT 1
        """), {"tid": track_id, "loc": location_id, "cam": camera_id}
    )).first()

    if row:
        # already active; optionally refresh representative fields (first image wins, or update if empty)
        stmt = text("""
            UPDATE person_sessions
            SET image_path = COALESCE(image_path, :img),
                attributes = COALESCE(attributes, CAST(:attrs AS jsonb)),
                attr_names = COALESCE(attr_names, CAST(:anames AS jsonb)),
                -- Ensure the parameter has a type even when NULL:
                attr_scores = COALESCE(CAST(:scores AS vector), attr_scores),
                embedding   = COALESCE(CAST(:emb AS vector), embedding)
            WHERE session_id = :sid
        """)

        params = {
            "img":    rep_image,                                  # str | None
            "attrs":  json.dumps(rep_attrs) if rep_attrs is not None else None,       # str | None
            "anames": json.dumps(rep_attr_names) if rep_attr_names is not None else None,  # str | None

            # For pgvector, pass a string literal like "[0.1,0.2,...]" or None
            "scores": (to_pgvector_literal(np.asarray(rep_scores, dtype="float32"))
                    if rep_scores is not None else None),
            "emb":    (to_pgvector_literal(np.asarray(rep_embedding, dtype="float32"))
                    if rep_embedding is not None else None),

            "sid":    row[0],  # the session_id you fetched
        }

        # IMPORTANT: pass a DICT (named params), NOT a tuple/list
        await s.execute(stmt, params)
        return

    ps = PersonSessionORM(
        id=_new_session_id(ts_ms),
        resolved_id=resolved_id,
        track_id=track_id,
        location_id=location_id,
        camera_id=camera_id,
        appear_ms=ts_ms,
        disappear_ms=None,
        attributes=rep_attrs if isinstance(rep_attrs, dict) else None,
        attr_names=rep_attr_names if isinstance(rep_attr_names, list) else None,
        image_path=rep_image
    )
    # Optional vectors (use ORM type if you mapped pgvector)
    setattr(ps, "attr_scores", rep_scores)
    setattr(ps, "embedding", rep_embedding)
    s.add(ps)

async def close_session_on_move_out(
    s: AsyncSession, track_id: str, location_id: str | None, camera_id: str | None, ts_ms: int
) -> None:
    await s.execute(
        text("""
            UPDATE person_sessions
            SET disappear_ms = :ts
            WHERE track_id = :tid
              AND COALESCE(location_id,'') = COALESCE(:loc,'')
              AND COALESCE(camera_id,'') = COALESCE(:cam,'')
              AND disappear_ms IS NULL
        """), {"ts": ts_ms, "tid": track_id, "loc": location_id, "cam": camera_id}
    )
