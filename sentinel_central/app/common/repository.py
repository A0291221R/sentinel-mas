# services/common/repository.py
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

def _check_unit_norm(v: np.ndarray, tol: float = 1e-3) -> bool:
    n = float(np.linalg.norm(v))
    return (1.0 - tol) <= n <= (1.0 + tol)

async def nearest_identity(
    s: AsyncSession,
    qvec: np.ndarray,
    topk: int = 5
) -> List[Dict[str, Any]]:
    """
    Return top identities by cosine distance.
    """
    rows = (await s.execute(
        text("""
        SELECT id, (embedding <=> (:q)::vector) AS distance, last_seen_ms, count_events
        FROM identities
        ORDER BY embedding <=> (:q)::vector
        LIMIT :k
        """),
        {"q": qvec.tolist(), "k": topk}
    )).mappings().all()
    return [dict(r) for r in rows]

async def upsert_identity(
    s: AsyncSession,
    resolved_id: str,
    qvec: np.ndarray,
    ts_ms: int,
    ema_alpha: float = 0.2
) -> None:
    """
    Update canonical embedding with EMA; else insert.
    """
    # Try fetch existing
    row = (await s.execute(
        text("SELECT embedding, count_events FROM identities WHERE id = :id"),
        {"id": resolved_id}
    )).first()

    if row:
        emb_db, count_ev = row[0], row[1]
        emb_np = np.asarray(emb_db, dtype=np.float32)
        new_emb = (1.0 - ema_alpha) * emb_np + ema_alpha * qvec
        # Re-normalize the canonical embedding to unit length
        new_emb = new_emb / (np.linalg.norm(new_emb) + 1e-12)
        await s.execute(
            text("""
                UPDATE identities
                SET embedding = :e, last_seen_ms = :ts, count_events = :c
                WHERE id = :id
            """),
            {"e": new_emb.tolist(), "ts": ts_ms, "c": int(count_ev) + 1, "id": resolved_id}
        )
    else:
        await s.execute(
            text("""
                INSERT INTO identities (id, embedding, created_ms, last_seen_ms, count_events)
                VALUES (:id, :e, :ts, :ts, 1)
            """),
            {"id": resolved_id, "e": qvec.tolist(), "ts": ts_ms}
        )

def _new_identity_id(ts_ms: int) -> str:
    import uuid
    return f"id_{ts_ms}_{uuid.uuid4().hex[:8]}"


async def _get_tracking_info(s, resolved_id: Optional[str]) -> tuple[bool, Optional[str]]:
    if not resolved_id:
        return (False, None)

    res = await s.execute(text("""
        SELECT is_tracked, annotation_name
        FROM identities
        WHERE id = :rid
        LIMIT 1
    """), {"rid": resolved_id})
    row = res.first()
    if not row:
        return (False, None)

    is_tracked = bool(row[0])
    name = row[1] if len(row) > 1 else None
    return (is_tracked, name)

class ResolutionResult(Tuple[str, float, Optional[float]]): ...
