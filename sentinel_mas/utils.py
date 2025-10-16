import numpy as np
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text_unit(query: str):
    emb = MODEL.encode(query).astype("float32")
    return to_unit_vec(emb)


def to_unit_vec(v: list[float] | np.ndarray) -> list[float]:
    a = np.asarray(v, dtype=np.float32)
    n = float(np.linalg.norm(a))
    if n < 1e-12:
        raise ValueError("Embedding norm is ~0 (cannot normalize).")
    return (a / n).tolist()