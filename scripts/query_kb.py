import argparse, psycopg
import numpy as np

from sentence_transformers import SentenceTransformer  # or OpenAI embeddings
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def to_unit_vec(v: list[float] | np.ndarray) -> list[float]:
    a = np.asarray(v, dtype=np.float32)
    n = float(np.linalg.norm(a))
    if n < 1e-12:
        raise ValueError("Embedding norm is ~0 (cannot normalize).")
    return (a / n).tolist()

def search_sop_cosine(query: str, k: int = 6):
    qvec = to_unit_vec(MODEL.encode(query).astype("float32"))  # normalize the query too!
    with psycopg.connect("postgresql://postgres:postgres@localhost:5432/sentinel") as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                id, section, title, text,
                embedding <=> %s::vector AS cos_dist
            FROM sop_chunks
            ORDER BY cos_dist ASC
            LIMIT %s
        """, (qvec, k))
        return [
            {"id": i, "section": s, "title": t, "text": x, "score": float(sc)}
            for (i, s, t, x, sc) in cur.fetchall()
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, required=True)
    parser.add_argument('--k', type=int, default=6)
    args = parser.parse_args()

    hits = search_sop_cosine(args.query, args.k)
    retrieved = [
        f"- [{h['section']}] {h['title']}: {h['text'][:160]} (score {h['score']:.2f})"
        for h in hits
    ]
    state = {
        "messages": [],
        "user_question": "How do I escalate a Level-2 anomaly?",
        "sop_context": "\n".join(retrieved),
    }
    print(state)




if __name__ == '__main__':
    main()    



