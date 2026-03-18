import numpy as np
import pytest

from services.rag.core.schemas import CaseRecord
from services.rag.services.index_manager import FAISSIndexManager


def _make_record(case_id: int) -> CaseRecord:
    return CaseRecord(
        case_id=case_id,
        policy_id=f"PLY-2024-{case_id:05d}",
        summary=f"test case {case_id}",
        outcome="claim approved",
        risk_tier="MODERATE",
        claim_amount=100_000.0,
    )


def _random_vectors(n: int, dim: int = 384) -> np.ndarray:
    rng = np.random.default_rng(42)
    vecs = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


def test_add_and_search() -> None:
    manager = FAISSIndexManager(dimension=384)
    vecs = _random_vectors(10)
    records = [_make_record(i) for i in range(10)]

    manager.add(vecs, records)
    assert manager.total_indexed == 10

    results = manager.search(vecs[0:1], top_k=3, threshold=0.0)
    assert len(results) > 0
    assert results[0].similarity_score >= results[-1].similarity_score


def test_search_empty_index() -> None:
    manager = FAISSIndexManager(dimension=384)
    query = _random_vectors(1)
    results = manager.search(query, top_k=5)
    assert results == []


def test_threshold_filters_low_scores() -> None:
    manager = FAISSIndexManager(dimension=384)
    vecs = _random_vectors(5)
    records = [_make_record(i) for i in range(5)]
    manager.add(vecs, records)

    # with a very high threshold, most random vectors won't match
    results = manager.search(vecs[0:1], top_k=5, threshold=0.99)
    # only the exact match (itself) should pass, with score ~1.0
    assert len(results) <= 1


def test_add_mismatched_counts() -> None:
    manager = FAISSIndexManager(dimension=384)
    vecs = _random_vectors(3)
    records = [_make_record(0)]

    with pytest.raises(ValueError, match="Vector count"):
        manager.add(vecs, records)


def test_save_and_load(tmp_path: object) -> None:
    path = str(tmp_path)
    index_file = f"{path}/test.faiss"
    store_file = f"{path}/test.json"

    manager = FAISSIndexManager(dimension=384)
    vecs = _random_vectors(5)
    records = [_make_record(i) for i in range(5)]
    manager.add(vecs, records)
    manager.save(index_file, store_file)

    loaded = FAISSIndexManager(dimension=384)
    loaded.load(index_file, store_file)
    assert loaded.total_indexed == 5
    assert len(loaded.cases) == 5

    results = loaded.search(vecs[0:1], top_k=3, threshold=0.0)
    assert len(results) > 0


def test_load_nonexistent_files() -> None:
    manager = FAISSIndexManager(dimension=384)
    manager.load("/nonexistent/path.faiss", "/nonexistent/store.json")
    assert manager.total_indexed == 0
