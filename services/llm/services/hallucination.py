import json

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock

from services.llm.core.schemas import SynthesisResult
from services.shared.schemas import HallucinationCheck

_JUDGE_PROMPT_TEMPLATE = """\
You are an auditor checking an insurance underwriting narrative for hallucinations.
A hallucination is any claim in the narrative that is NOT supported by the source data below.

SOURCE DATA:
- Entity summary: {entity_summary}
- Predicted risk tier: {risk_tier}
- Risk probability: {risk_probability}
- Predicted claim amount: ${predicted_claim_amount:,.2f}
- Key risk factors: {risk_factors}
- Similar cases retrieved: {similar_cases}

NARRATIVE TO AUDIT:
{narrative}

Check for these hallucination types:
1. Fabricated facts: dollar amounts, percentages, or statistics not in the source data
2. Ghost references: policy IDs, case references, or risk factors not in the source data
3. Unsupported conclusions: causal claims not derivable from the entity summary

Respond with ONLY valid JSON (no markdown, no explanation):
{{"hallucination_detected": true/false, "hallucination_count": <int>, "details": [<list of specific hallucinated claims>], "confidence": <float 0-1>}}"""

_SAFE_DEFAULT = HallucinationCheck(detected=False, count=0, flags=[], confidence=0.0)


def _build_prompt(
    narrative: str,
    entity_summary: dict[str, list[str]],
    result: SynthesisResult,
) -> str:
    return _JUDGE_PROMPT_TEMPLATE.format(
        entity_summary=json.dumps(entity_summary),
        risk_tier=result.risk_tier,
        risk_probability=result.risk_probability,
        predicted_claim_amount=result.predicted_claim_amount,
        risk_factors=json.dumps([rf.model_dump() for rf in result.key_risk_factors]),
        similar_cases=json.dumps([sc.model_dump() for sc in result.similar_cases]),
        narrative=narrative,
    )


async def detect_hallucinations(
    narrative: str,
    entity_summary: dict[str, list[str]],
    result: SynthesisResult,
    api_key: str,
    model: str,
) -> HallucinationCheck:
    """Call a Claude judge to check whether the narrative hallucinates.

    Returns a safe default (detected=False) on any error so the main
    synthesis response is never blocked by a failing judge call.
    """
    client = AsyncAnthropic(api_key=api_key)
    prompt = _build_prompt(narrative, entity_summary, result)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = next(
            (b.text for b in response.content if isinstance(b, TextBlock)),
            None,
        )
        if raw is None:
            return _SAFE_DEFAULT
        data = json.loads(raw)
        return HallucinationCheck(
            detected=bool(data.get("hallucination_detected", False)),
            count=int(data.get("hallucination_count", 0)),
            flags=list(data.get("details", [])),
            confidence=float(data.get("confidence", 0.0)),
        )
    except Exception:
        return _SAFE_DEFAULT
