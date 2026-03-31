import time

import httpx
import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.llm.api.dependencies import get_http_client, get_provider, get_settings
from services.llm.config import LLMSettings
from services.llm.core.schemas import SynthesisRequest
from services.llm.services.hallucination import detect_hallucinations
from services.llm.services.provider import LLMProvider
from services.shared.exceptions import SynthesisError
from services.shared.schemas import SubmissionAnalysis

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["llm"])

_hallucination_checks = Counter(
    "aria_hallucination_checks_total",
    "Hallucination detection outcomes",
    ["detected"],
)
_hallucination_confidence = Histogram(
    "aria_hallucination_confidence",
    "Hallucination judge confidence scores",
    buckets=[0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0],
)


@router.post("/synthesize", response_model=SubmissionAnalysis)
@limiter.limit("10/minute")
async def synthesize(
    request: Request,
    body: SynthesisRequest,
    settings: LLMSettings = Depends(get_settings),
    provider: LLMProvider = Depends(get_provider),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> SubmissionAnalysis | JSONResponse:
    start = time.perf_counter()

    await logger.ainfo(
        "synthesis_started",
        submission_id=body.submission_id,
        provider=settings.provider,
        entity_count=sum(len(v) for v in body.entity_summary.values()),
    )

    try:
        result = await provider.synthesize(
            body.entity_summary, body.full_text, http_client, settings
        )
    except SynthesisError as exc:
        await logger.aerror(
            "synthesis_failed",
            error=str(exc),
            submission_id=body.submission_id,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Synthesis failed", "detail": str(exc)},
        )

    hallucination_check = None
    if settings.enable_hallucination_check and settings.anthropic_api_key:
        hallucination_check = await detect_hallucinations(
            result.underwriter_narrative,
            body.entity_summary,
            result,
            settings.anthropic_api_key,
            settings.anthropic_model,
        )

    if hallucination_check is not None:
        _hallucination_checks.labels(detected=str(hallucination_check.detected).lower()).inc()
        _hallucination_confidence.observe(hallucination_check.confidence)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    analysis = SubmissionAnalysis(
        submission_id=body.submission_id,
        risk_tier=result.risk_tier,
        risk_probability=result.risk_probability,
        predicted_claim_amount=result.predicted_claim_amount,
        key_risk_factors=result.key_risk_factors,
        underwriter_narrative=result.underwriter_narrative,
        similar_cases=result.similar_cases,
        confidence_score=result.confidence_score,
        processing_time_ms=elapsed_ms,
        hallucination_check=hallucination_check,
    )

    await logger.ainfo(
        "synthesis_complete",
        submission_id=body.submission_id,
        risk_tier=analysis.risk_tier,
        processing_time_ms=elapsed_ms,
    )
    return analysis
