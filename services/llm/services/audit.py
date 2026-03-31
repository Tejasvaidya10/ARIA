import json
from datetime import UTC, datetime
from pathlib import Path

import structlog

from services.shared.schemas import SubmissionAnalysis

logger = structlog.get_logger()

open = open


async def record(analysis: SubmissionAnalysis, audit_log_path: str, provider: str) -> None:
    request_id = structlog.contextvars.get_contextvars().get("request_id", "")

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": request_id,
        "submission_id": analysis.submission_id,
        "risk_tier": str(analysis.risk_tier),
        "risk_probability": analysis.risk_probability,
        "predicted_claim_amount": analysis.predicted_claim_amount,
        "confidence_score": analysis.confidence_score,
        "processing_time_ms": analysis.processing_time_ms,
        "similar_cases_count": len(analysis.similar_cases),
        "hallucination_detected": analysis.hallucination_check.detected
        if analysis.hallucination_check
        else None,
        "hallucination_confidence": analysis.hallucination_check.confidence
        if analysis.hallucination_check
        else None,
        "provider": provider,
    }

    await logger.ainfo("audit_trail", **event)

    try:
        path = Path(audit_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as exc:
        await logger.awarning("audit_write_failed", error=str(exc))
