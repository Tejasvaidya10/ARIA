import numpy as np

from services.rag.services.embedder import (
    embed_batch,
    embed_text,
    entities_to_text,
    load_embedding_model,
)


def test_entities_to_text_basic(sample_entity_summary: dict[str, list[str]]) -> None:
    text = entities_to_text(sample_entity_summary)
    assert "peril: fire" in text
    assert "coverage_type: general liability" in text
    assert "property_type: warehouse" in text


def test_entities_to_text_empty(empty_entity_summary: dict[str, list[str]]) -> None:
    text = entities_to_text(empty_entity_summary)
    assert text == "empty submission"


def test_entities_to_text_sorted_labels() -> None:
    entities = {"PERIL": ["fire"], "COVERAGE_TYPE": ["property"]}
    text = entities_to_text(entities)
    cov_pos = text.index("coverage_type")
    peril_pos = text.index("peril")
    assert cov_pos < peril_pos, "labels should be sorted alphabetically"


def test_embed_text_shape() -> None:
    model = load_embedding_model("all-MiniLM-L6-v2")
    vec = embed_text(model, "fire and flood exposure")
    assert vec.shape == (1, 384)
    assert vec.dtype == np.float32


def test_embed_batch_shape() -> None:
    model = load_embedding_model("all-MiniLM-L6-v2")
    texts = ["fire exposure", "flood risk", "cyber liability"]
    vecs = embed_batch(model, texts)
    assert vecs.shape == (3, 384)


def test_normalized_vectors() -> None:
    """Normalized vectors should have unit length (L2 norm ~= 1.0)."""
    model = load_embedding_model("all-MiniLM-L6-v2")
    vec = embed_text(model, "warehouse with fire risk")
    norm = float(np.linalg.norm(vec))
    assert abs(norm - 1.0) < 0.01
