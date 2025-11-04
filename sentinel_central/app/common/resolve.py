from typing import Optional, Tuple, List, Dict, Any
import uuid
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils import from_pgvector_value, to_pgvector_literal, unit

def _unit(v: np.ndarray) -> np.ndarray:
    v = v.astype(np.float32, copy=False)
    n = float(np.linalg.norm(v))
    if n == 0:
        return v
    return v / n

def _new_identity_id(ts_ms: int) -> str:
    return f"id_{ts_ms}_{uuid.uuid4().hex[:8]}"

async def _nearest_identities(s, qvec: np.ndarray, k: int = 2):
    rows = (await s.execute(
        text("""
            SELECT id, (embedding <=> (:q)::vector) AS distance
            FROM identities
            ORDER BY embedding <=> (:q)::vector
            LIMIT :k
        """),
        {
            "q": to_pgvector_literal(qvec),  # <-- string, not list
            "k": k
        }
    )).mappings().all()
    return [dict(r) for r in rows]

async def _upsert_identity(s, rid: str, emb: np.ndarray, ts_ms: int, ema_alpha: float = 0.2) -> None:
    emb = unit(emb)

    row = (await s.execute(
        text("SELECT embedding, count_events FROM identities WHERE id = :id"),
        {"id": rid}
    )).mappings().first()

    if row:
        base = from_pgvector_value(row["embedding"])
        new_emb = unit((1.0 - ema_alpha) * base + ema_alpha * emb)
        e_str = to_pgvector_literal(new_emb)
        await s.execute(
            text("""
                UPDATE identities
                SET embedding = (:e)::vector,
                    last_seen_ms = :ts,
                    count_events = :c
                WHERE id = :id
            """),
            {"e": e_str, "ts": ts_ms, "c": int(row["count_events"]) + 1, "id": rid}
        )
    else:
        e_str = to_pgvector_literal(emb)
        await s.execute(
            text("""
                INSERT INTO identities (id, annotation_name, embedding, created_ms, last_seen_ms, count_events)
                VALUES (:id, :anno_name, (:e)::vector, :ts, :ts, 1)
            """),
            {"id": rid, "anno_name": rid, "e": e_str, "ts": ts_ms}
        )
        
class Resolver:
    """
    Decision policy:
      - If best ≤ tau_same  -> match best_id
      - Else if best ≤ tau_ambig and (second - best) ≥ delta_min -> match best_id
      - Else -> NEW ID
    """
    def __init__(self, tau_same: float = 0.22, tau_ambig: float = 0.30, delta_min: float = 0.05):
        self.tau_same = tau_same
        self.tau_ambig = tau_ambig
        self.delta_min = delta_min

    async def resolve(self, s: AsyncSession, qvec: np.ndarray, ts_ms: int) -> Tuple[str, float, Optional[float], bool]:
        """
        Returns (resolved_id, best_distance, second_distance|None, is_new_identity)
        """
        qvec = _unit(qvec)

        top = await _nearest_identities(s, qvec, k=2)
        if not top:
            rid = _new_identity_id(ts_ms)
            await _upsert_identity(s, rid, qvec, ts_ms)
            return rid, 1.0, None, True

        best = float(top[0]["distance"])
        second = float(top[1]["distance"]) if len(top) > 1 else None
        best_id = top[0]["id"]

        if best <= self.tau_same:
            rid = best_id
            is_new = False
        elif best <= self.tau_ambig and (second is None or (second - best) >= self.delta_min):
            rid = best_id
            is_new = False
        else:
            rid = _new_identity_id(ts_ms)
            is_new = True

        await _upsert_identity(s, rid, qvec, ts_ms)
        return rid, best, second, is_new
