from __future__ import annotations

from typing import Any, Dict, List, Optional

import psycopg

# Choose the import that matches your LangChain version:
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from sentinel_mas.config import Config

from ..utils import embed_text_unit

DSN = Config.SENTINEL_DB_URL
print(f"sop_tools, DSN: {DSN}")


# --------- helpers ----------
def _row_to_hit(r: Any) -> Dict[str, Any]:
    return {
        "id": r[0],
        "section": r[1],
        "title": r[2],
        "text": r[3],
        "cos_sim": float(r[4]),
    }


# --------- arg schemas (stable across LC versions) ----------
class SearchSOPArgs(BaseModel):
    query: str = Field(..., description="User query to search the SOP KB.")
    k: int = Field(
        6, ge=1, le=50, description="Number of top matches to return (1–50)."
    )


class GetSOPArgs(BaseModel):
    id_or_section: str = Field(
        ...,
        description="SOP id (e.g., 'SOP-1') or section (e.g., '3.2.1').",
    )


# --------- tools ----------
@tool(args_schema=SearchSOPArgs)
def search_sop(query: str, k: int = 6) -> List[Dict[str, Any]]:
    """Search SOP KB by cosine similarity
    (unit-normalized embeddings + vector_cosine_ops)."""
    qvec = embed_text_unit(query)
    sql = """
    SELECT id, section, title, text,
           1 - (embedding <=> %s::vector) AS cos_sim
    FROM sop_chunks
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    # You can add autocommit=True if you prefer: psycopg.connect(DSN, autocommit=True)
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(sql, (qvec, qvec, k))
        return [_row_to_hit(r) for r in cur.fetchall()]


@tool(args_schema=GetSOPArgs)
def get_sop(id_or_section: str) -> Optional[Dict[str, Any]]:
    """Fetch the SOP record by id ('SOP-1') or section ('3.2.1') from sop_chunks."""
    sql = """
    SELECT id, section, title, text, tags, updated_at,
           NULL::jsonb AS full_json
    FROM sop_chunks
    WHERE id = %s OR section = %s
    LIMIT 1;
    """
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(sql, (id_or_section, id_or_section))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0],
            "section": r[1],
            "title": r[2],
            "text": r[3],
            "tags": r[4],
            "updated_at": str(r[5]) if r[5] is not None else None,
            "full": r[6],
        }
