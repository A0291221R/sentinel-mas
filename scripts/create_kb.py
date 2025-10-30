import argparse

import json, psycopg, numpy as np
from sentence_transformers import SentenceTransformer  # or OpenAI embeddings

MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def yield_chunks(jsonl_path):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            # use chunk_text for retrieval, but also embed title+steps
            text = f"{row['title']} — {row['chunk_text']}"
            yield row["id"], row["section"], row["title"], text, row

def to_unit_vec(v: list[float] | np.ndarray) -> list[float]:
    a = np.asarray(v, dtype=np.float32)
    n = float(np.linalg.norm(a))
    if n < 1e-12:
        raise ValueError("Embedding norm is ~0 (cannot normalize).")
    return (a / n).tolist()

# uv run ./scripts/create_kb.py --kb sentinel_mas/data/kb/sentinel_sop_kb.jsonl 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kb', type=str, required=True)
    args = parser.parse_args()

    print(args.kb)

    # Example: create vectors in-memory
    docs = []
    vecs = []
    meta = []
    for _id, sec, title, text, raw in yield_chunks(args.kb):
        emb = MODEL.encode(text).astype("float32")  # 384-dim for MiniLM
        emb_u = to_unit_vec(emb)
        docs.append((_id, sec, title, text))
        vecs.append(emb_u)
        meta.append(raw)


    with psycopg.connect("postgresql://postgres:postgres@localhost:5432/sentinel") as conn:
        with conn.cursor() as cur:
            for (_id, sec, title, text), emb_u, raw in zip(docs, vecs, meta):
                cur.execute(
                    """
                    INSERT INTO sop_chunks (id, section, title, text, tags, updated_at, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET section=EXCLUDED.section, title=EXCLUDED.title, text=EXCLUDED.text,
                        tags=EXCLUDED.tags, updated_at=EXCLUDED.updated_at, embedding=EXCLUDED.embedding;
                    """,
                    (
                        _id, sec, title, text,
                        raw.get("tags", []),
                        raw.get("updated_at"),
                        emb_u,  # psycopg adapts Python arrays to pgvector
                    ),
                )

if __name__ == '__main__':
    main()