class ARIAError(Exception):
    """Base exception for all ARIA errors."""


class ModelNotLoadedError(ARIAError):
    """Raised when a model artifact hasn't been loaded yet."""


class ExtractionError(ARIAError):
    """Raised when PDF text extraction or NER fails."""


class PredictionError(ARIAError):
    """Raised when the XGBoost prediction pipeline fails."""


class EmbeddingError(ARIAError):
    """Raised when the embedding or vector search fails."""


class SynthesisError(ARIAError):
    """Raised when the LLM synthesis step fails."""
