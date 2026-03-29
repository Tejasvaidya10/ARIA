from typing import Any

import httpx
from fastapi.testclient import TestClient

from services.llm.config import LLMSettings
from services.llm.core.schemas import SynthesisResult
from services.llm.services.tools import execute_tool
from services.shared.schemas import RiskFactor, RiskTier, SimilarCase

FIRE_SUBMISSION: dict[str, list[str]] = {
    "PERIL": ["fire", "smoke"],
    "MONEY": ["$75,000", "$500,000"],
    "COVERAGE_TYPE": ["commercial property"],
    "PROPERTY_TYPE": ["wood-frame office"],
}


class ServiceRouter(httpx.AsyncBaseTransport):
    """Routes LLM service's outbound httpx calls to in-process TestClients.

    Keyed by base URL (e.g. "http://localhost:8001"). Stores the headers
    of the most recent forwarded request for inspection in tests.
    """

    def __init__(self, routes: dict[str, TestClient]) -> None:
        self.routes = routes
        self.last_request_headers: dict[str, str] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        base = f"{request.url.scheme}://{request.url.host}:{request.url.port}"
        client = self.routes.get(base)
        if client is None:
            raise httpx.ConnectError(f"No test route configured for {base}")

        self.last_request_headers = dict(request.headers)
        response = client.request(
            method=request.method,
            url=request.url.path,
            content=request.content,
            headers=dict(request.headers),
        )
        return httpx.Response(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )


class PassthroughProvider:
    """LLM provider that calls real downstream tools but returns a canned narrative.

    Used in integration tests to exercise the full prediction + RAG pipeline
    without making any Claude API or Ollama calls.
    """

    async def synthesize(
        self,
        entity_summary: dict[str, list[str]],
        full_text: str,
        http_client: httpx.AsyncClient,
        settings: Any,
    ) -> SynthesisResult:
        if not isinstance(settings, LLMSettings):
            settings = LLMSettings()

        pred = await execute_tool(
            "get_risk_prediction",
            {"entity_summary": entity_summary, "submission_id": "passthrough"},
            http_client,
            settings,
        )
        rag = await execute_tool(
            "get_similar_cases",
            {"entity_summary": entity_summary},
            http_client,
            settings,
        )

        factors = [
            RiskFactor(
                name=f["name"],
                shap_value=f["shap_value"],
                direction=f["direction"],
            )
            for f in pred.get("key_risk_factors", [])
        ]

        raw_cases = rag.get("results") or rag.get("similar_cases", [])
        cases = [
            SimilarCase(
                policy_id=c["policy_id"],
                similarity_score=c["similarity_score"],
                summary=c["summary"],
                outcome=c.get("outcome"),
            )
            for c in raw_cases
        ]

        return SynthesisResult(
            risk_tier=RiskTier(pred.get("risk_tier", "MODERATE")),
            risk_probability=float(pred.get("risk_probability", 0.5)),
            predicted_claim_amount=float(pred.get("predicted_claim_amount", 0.0)),
            key_risk_factors=factors,
            underwriter_narrative="Integration test passthrough narrative.",
            similar_cases=cases,
            confidence_score=float(pred.get("confidence_score", 0.5)),
        )
