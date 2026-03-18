import json
from pathlib import Path

import faiss
import numpy as np

from services.rag.core.schemas import CaseRecord, SearchResult


class FAISSIndexManager:
    """Manages a FAISS vector index and its associated case metadata.

    FAISS only stores vectors and integer IDs. The actual case data
    (policy_id, summary, outcome) lives in a separate dict keyed by
    those same integer IDs. Both are saved/loaded together.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        # IndexFlatIP = brute-force inner product search.
        # With normalized vectors, inner product == cosine similarity.
        # Fine for <100k vectors. Switch to IndexIVFFlat for millions.
        self.index = faiss.IndexFlatIP(dimension)
        self.cases: dict[int, CaseRecord] = {}
        self._next_id = 0

    @property
    def total_indexed(self) -> int:
        count: int = self.index.ntotal
        return count

    def add(self, vectors: np.ndarray, records: list[CaseRecord]) -> None:  # type: ignore[type-arg]
        """Add vectors and their corresponding case records to the index."""
        if vectors.shape[0] != len(records):
            msg = f"Vector count ({vectors.shape[0]}) != record count ({len(records)})"
            raise ValueError(msg)

        for record in records:
            self.cases[self._next_id] = record
            self._next_id += 1

        self.index.add(vectors)

    def search(
        self,
        query_vector: np.ndarray,  # type: ignore[type-arg]
        top_k: int = 5,
        threshold: float = 0.3,
    ) -> list[SearchResult]:
        """Find the top-k most similar cases to the query vector."""
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)

        results: list[SearchResult] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx == -1 or score < threshold:
                continue
            case = self.cases.get(int(idx))
            if case is None:
                continue
            results.append(
                SearchResult(
                    policy_id=case.policy_id,
                    similarity_score=round(float(score), 4),
                    summary=case.summary,
                    outcome=case.outcome,
                )
            )

        return results

    def save(self, index_path: str, store_path: str) -> None:
        """Persist the FAISS index and case metadata to disk."""
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(store_path).parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, index_path)

        serializable = {str(k): v.model_dump() for k, v in self.cases.items()}
        metadata = {"next_id": self._next_id, "cases": serializable}
        Path(store_path).write_text(json.dumps(metadata, indent=2))

    def load(self, index_path: str, store_path: str) -> None:
        """Load a previously saved FAISS index and case metadata."""
        if not Path(index_path).exists() or not Path(store_path).exists():
            return

        self.index = faiss.read_index(index_path)

        raw = json.loads(Path(store_path).read_text())
        self._next_id = raw["next_id"]
        self.cases = {int(k): CaseRecord(**v) for k, v in raw["cases"].items()}
