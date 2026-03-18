import json
from typing import Any

import httpx
import structlog

from services.llm.config import LLMSettings
from services.llm.core.schemas import SynthesisResult
from services.llm.services.tools import (
    SYSTEM_PROMPT,
    execute_tool,
    format_tool_results_prompt,
)
from services.shared.exceptions import SynthesisError
from services.shared.schemas import RiskFactor, RiskTier, SimilarCase

logger = structlog.get_logger()


class OllamaProvider:
    """Local LLM provider using Ollama's HTTP API.

    Unlike the Anthropic provider, this doesn't use tool-use (local models
    handle it poorly). Instead, it calls prediction and RAG directly via
    HTTP, formats the results into a prompt, and asks the model to write
    the narrative.
    """

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def synthesize(
        self,
        entity_summary: dict[str, list[str]],
        full_text: str,
        http_client: httpx.AsyncClient,
        settings: LLMSettings,
    ) -> SynthesisResult:
        # Call both downstream services directly
        await logger.ainfo("calling_prediction_service")
        prediction = await execute_tool(
            "get_risk_prediction",
            {"entity_summary": entity_summary, "submission_id": "ollama-run"},
            http_client,
            settings,
        )

        await logger.ainfo("calling_rag_service")
        search = await execute_tool(
            "get_similar_cases",
            {"entity_summary": entity_summary, "top_k": 5},
            http_client,
            settings,
        )

        # Build the prompt with all data baked in
        context = format_tool_results_prompt(prediction, search)
        entities_text = json.dumps(entity_summary, indent=2)
        prompt = f"Submission entities:\n{entities_text}\n\n{context}"
        if full_text:
            prompt = f"Submission text (first 2000 chars):\n{full_text[:2000]}\n\n{prompt}"

        narrative = await self._generate(prompt, settings.request_timeout)
        return self._build_result(narrative, prediction, search)

    async def _generate(self, prompt: str, timeout: float) -> str:
        """Call Ollama's generate endpoint."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
        }

        try:
            resp = await httpx.AsyncClient().post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")  # type: ignore[no-any-return]
        except httpx.HTTPError as exc:
            raise SynthesisError(f"Ollama request failed: {exc}") from exc

    def _build_result(
        self,
        narrative: str,
        prediction: dict[str, Any],
        search: dict[str, Any],
    ) -> SynthesisResult:
        risk_factors = [RiskFactor(**rf) for rf in prediction.get("key_risk_factors", [])]
        similar_cases = [
            SimilarCase(
                policy_id=r.get("policy_id", "unknown"),
                similarity_score=r.get("similarity_score", 0.0),
                summary=r.get("summary", ""),
                outcome=r.get("outcome"),
            )
            for r in search.get("results", [])
        ]

        return SynthesisResult(
            risk_tier=RiskTier(prediction.get("risk_tier", "MODERATE")),
            risk_probability=prediction.get("risk_probability", 0.5),
            predicted_claim_amount=prediction.get("predicted_claim_amount", 0.0),
            key_risk_factors=risk_factors,
            underwriter_narrative=narrative,
            similar_cases=similar_cases,
            confidence_score=prediction.get("confidence_score", 0.5),
        )
