import numpy as np
from sentence_transformers import SentenceTransformer


def load_embedding_model(model_name: str) -> SentenceTransformer:
    """Load a sentence-transformers model.

    Downloads on first run (~80MB for MiniLM), cached after that.
    Runs entirely on CPU — no GPU needed.
    """
    return SentenceTransformer(model_name)


def entities_to_text(entity_summary: dict[str, list[str]]) -> str:
    """Flatten an entity summary dict into a single searchable string.

    The embedding model needs raw text, not structured data. We concatenate
    all entity labels and values so semantically similar cases produce
    similar vectors. The label prefixes (e.g. "peril:") help the model
    distinguish between a peril named "fire" and a coverage named "fire".
    """
    parts: list[str] = []
    for label, values in sorted(entity_summary.items()):
        for val in values:
            parts.append(f"{label.lower()}: {val}")
    return "; ".join(parts) if parts else "empty submission"


def embed_text(model: SentenceTransformer, text: str) -> np.ndarray:
    """Encode a single text string into a dense vector."""
    embedding = model.encode(text, normalize_embeddings=True)
    return np.array(embedding, dtype=np.float32).reshape(1, -1)


def embed_batch(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    """Encode multiple texts at once. More efficient than one-by-one."""
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=64)
    return np.array(embeddings, dtype=np.float32)
