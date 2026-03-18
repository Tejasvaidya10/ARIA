import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.rag.api.dependencies import get_embedding_model, get_index_manager, get_settings
from services.rag.config import RAGSettings
from services.rag.core.schemas import SearchRequest, SearchResponse
from services.rag.services.embedder import embed_text, entities_to_text
from services.rag.services.index_manager import FAISSIndexManager

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def _run_search(
    request_data: SearchRequest,
    model: Any,
    manager: FAISSIndexManager,
    threshold: float,
) -> SearchResponse:
    """Synchronous search logic, meant to run in a thread."""
    query_text = entities_to_text(request_data.entity_summary)
    query_vector = embed_text(model, query_text)
    results = manager.search(query_vector, top_k=request_data.top_k, threshold=threshold)

    return SearchResponse(
        query_text=query_text,
        results=results,
        total_indexed=manager.total_indexed,
    )


@router.post("/search", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_similar_cases(
    request: Request,
    body: SearchRequest,
    settings: RAGSettings = Depends(get_settings),
    model: Any = Depends(get_embedding_model),
    manager: FAISSIndexManager = Depends(get_index_manager),
) -> SearchResponse:
    """Find historical cases similar to the given entity summary.

    Embeds the entity summary, then searches the FAISS index for the
    closest vectors. Returns cases above the similarity threshold.
    """
    return await asyncio.to_thread(
        _run_search, body, model, manager, settings.similarity_threshold
    )
