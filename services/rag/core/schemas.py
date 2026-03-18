from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    entity_summary: dict[str, list[str]]
    top_k: int = Field(default=5, ge=1, le=20)


class CaseRecord(BaseModel):
    """A historical insurance case stored alongside its FAISS vector."""

    case_id: int
    policy_id: str
    summary: str
    outcome: str
    risk_tier: str
    claim_amount: float


class SearchResult(BaseModel):
    policy_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    summary: str
    outcome: str


class SearchResponse(BaseModel):
    query_text: str
    results: list[SearchResult]
    total_indexed: int
