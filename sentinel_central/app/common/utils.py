
import numpy as np
from typing import Sequence, Union

def unit(v: np.ndarray) -> np.ndarray:
    v = v.astype(np.float32, copy=False)
    n = float(np.linalg.norm(v))
    return v if n == 0 else (v / n)

def to_pgvector_literal(v: np.ndarray) -> str:
    v = v.astype(np.float32, copy=False)
    return "[" + ",".join(format(float(x), ".8f") for x in v.tolist()) + "]"

def from_pgvector_value(x: Union[str, Sequence[float], np.ndarray]) -> np.ndarray:
    if isinstance(x, np.ndarray):
        return x.astype(np.float32, copy=False)
    if isinstance(x, (list, tuple)):
        return np.asarray(x, dtype=np.float32)
    if isinstance(x, str):
        s = x.strip()
        if s and s[0] == "[" and s[-1] == "]":
            s = s[1:-1]
        return np.asarray([float(t) for t in s.split(",") if t], dtype=np.float32)
    raise TypeError(f"Unsupported pgvector value type: {type(x)}")
