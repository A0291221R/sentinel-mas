import numpy as np
import pytest

@pytest.fixture(autouse=True)
def patch_sentence_transformer(monkeypatch):
    """Patch SentenceTransformer to avoid model download and heavy init."""
    class FakeModel:
        def encode(self, text):
            # deterministic "embedding"
            return np.array([1.0, 2.0, 2.0], dtype=np.float32)
    monkeypatch.setattr(
        "sentinel_mas.utils.SentenceTransformer",
        lambda name="all-MiniLM-L6-v2": FakeModel(),
    )
    # prevent reloading existing MODEL global (if already imported)
    monkeypatch.setattr("sentinel_mas.utils.MODEL", FakeModel())
    yield

def test_to_unit_vec_normalization():
    from sentinel_mas.utils import to_unit_vec
    v = np.array([3, 4], dtype=np.float32)
    out = to_unit_vec(v)
    assert np.allclose(np.linalg.norm(out), 1.0, atol=1e-6)
    assert isinstance(out, list)

def test_to_unit_vec_zero_norm_raises():
    from sentinel_mas.utils import to_unit_vec
    with pytest.raises(ValueError):
        to_unit_vec([0.0, 0.0, 0.0])

def test_embed_text_unit(monkeypatch):
    from sentinel_mas import utils
    res = utils.embed_text_unit("hello world")
    # The fake model returns [1,2,2], unit length → [0.333, 0.667, 0.667]
    assert isinstance(res, list)
    assert np.allclose(np.linalg.norm(res), 1.0, atol=1e-6)
