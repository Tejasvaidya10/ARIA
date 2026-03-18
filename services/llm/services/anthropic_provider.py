import json
from typing import Any

import httpx
import structlog
from anthropic import AsyncAnthropic

from services.llm.config import LLMSettings
from services.llm.core.schemas import SynthesisResult
from services.llm.services.tools import SYSTEM_PROMPT, TOOL_DEFINITIONS, execute_tool
from services.shared.exceptions import SynthesisError
from services.shared.schemas import RiskFactor, RiskTier, SimilarCase

logger = structlog.get_logger()


class AnthropicProvider:
    """Claude-based LLM provider using the Anthropic Messages API with tool-use.

    Claude receives entity data and tool definitions, decides which tools to
    call (prediction, RAG), gets results back, then writes the underwriter
    narrative. The tool-use loop continues until Claude stops calling tools
    or we hit max_tool_rounds.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def synthesize(
        self,
        entity_summary: dict[str, list[str]],
        full_text: str,
        http_client: httpx.AsyncClient,
        settings: LLMSettings,
    ) -> SynthesisResult:
        user_message = (
            f"Analyze this insurance submission.\n\n"
            f"Extracted entities:\n{json.dumps(entity_summary, indent=2)}"
        )
        if full_text:
            user_message += f"\n\nRaw submission text (first 2000 chars):\n{full_text[:2000]}"

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

        prediction_data: dict[str, Any] = {}
        search_data: dict[str, Any] = {}

        for round_num in range(settings.max_tool_rounds):
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            if response.stop_reason == "end_turn":
                narrative = self._extract_text(response.content)
                break

            if response.stop_reason != "tool_use":
                await logger.awarning(
                    "unexpected_stop_reason",
                    stop_reason=response.stop_reason,
                    round=round_num,
                )
                narrative = self._extract_text(response.content)
                break

            # Process tool calls from this turn
            messages.append({"role": "assistant", "content": response.content})  # type: ignore[arg-type]
            tool_results: list[dict[str, Any]] = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                await logger.ainfo("executing_tool", tool=block.name, round=round_num)
                result = await execute_tool(block.name, block.input, http_client, settings)  # type: ignore[arg-type]

                if block.name == "get_risk_prediction":
                    prediction_data = result
                elif block.name == "get_similar_cases":
                    search_data = result

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})
        else:
            raise SynthesisError(f"Tool-use loop exceeded {settings.max_tool_rounds} rounds")

        return self._build_result(narrative, prediction_data, search_data)

    def _extract_text(self, content: Any) -> str:
        """Pull the text content from Claude's response blocks."""
        for block in content:
            if block.type == "text":
                return block.text  # type: ignore[no-any-return]
        return ""

    def _build_result(
        self,
        narrative: str,
        prediction: dict[str, Any],
        search: dict[str, Any],
    ) -> SynthesisResult:
        """Assemble a SynthesisResult from tool outputs and Claude's narrative."""
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
