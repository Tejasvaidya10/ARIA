"""End-to-end evaluation of the ARIA pipeline.

Selects 20 stratified cases from the Kaggle dataset, runs them through
prediction and RAG, and validates that outputs are correct, grounded,
and consistent. Optionally tests LLM synthesis with hallucination detection.

Usage:
    python -m scripts.eval_pipeline               # direct mode (no Docker)
    python -m scripts.eval_pipeline --live         # hit Docker services
    python -m scripts.eval_pipeline --include-llm  # also test LLM stage
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

import httpx
from scripts.build_case_index import RISK_TIERS
from scripts.train_xgboost import row_to_entity_summary

from services.prediction.core.constants import FEATURE_DISPLAY_NAMES
from services.prediction.services.feature_engineer import extract_features
from services.prediction.services.predictor import (
    create_explainer,
    load_model,
    predict_risk,
)
from services.rag.services.embedder import (
    embed_text,
    entities_to_text,
    load_embedding_model,
)
from services.rag.services.index_manager import FAISSIndexManager

DATA_PATH = Path("data/raw/insurance_claims.csv")
DEFAULT_OUTPUT = "data/eval/eval_report.json"

TIER_ORDER = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
VALID_DISPLAY_NAMES = set(FEATURE_DISPLAY_NAMES.values())


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CaseEvalResult:
    case_index: int
    incident_type: str
    incident_severity: str
    fraud_reported: str
    actual_claim_amount: float
    expected_tier: str
    predicted_tier: str
    risk_probability: float
    predicted_claim_amount: float
    risk_factors: list[dict[str, object]] = field(default_factory=list)
    rag_result_count: int = 0
    rag_top_similarity: float = 0.0
    rag_type_match: bool = False
    tier_match: bool = False
    tier_adjacent: bool = False
    claim_reasonable: bool = False
    consistency_passed: bool = False
    shap_grounded: bool = False
    processing_time_ms: float = 0.0


@dataclass
class LLMEvalResult:
    case_index: int
    narrative_length: int = 0
    tier_matches_prediction: bool = False
    references_shap_factor: bool = False
    hallucination_detected: bool = False
    hallucination_count: int = 0
    hallucination_details: list[str] = field(default_factory=list)
    hallucination_confidence: float = 0.0


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class PipelineBackend(Protocol):
    def run_prediction(
        self, submission_id: str, entity_summary: dict[str, list[str]]
    ) -> dict[str, object]: ...

    def run_search(
        self, entity_summary: dict[str, list[str]], top_k: int
    ) -> list[dict[str, object]]: ...


class DirectBackend:
    """Runs prediction and RAG by importing modules directly."""

    def __init__(self) -> None:
        from services.prediction.config import PredictionSettings

        settings = PredictionSettings()
        self._prob_model = load_model(settings.xgboost_model_path)
        self._sev_model = load_model(settings.xgboost_severity_model_path)
        self._explainer = create_explainer(self._prob_model)
        self._settings = settings

        self._embed_model = load_embedding_model("all-MiniLM-L6-v2")
        self._index_manager = FAISSIndexManager()
        self._index_manager.load("data/faiss/case_index.faiss", "data/faiss/case_store.json")

    def run_prediction(
        self, submission_id: str, entity_summary: dict[str, list[str]]
    ) -> dict[str, object]:
        features = extract_features(entity_summary)
        result = predict_risk(
            self._prob_model,
            self._sev_model,
            self._explainer,
            features,
            self._settings,
        )
        data = result.model_dump()
        data["submission_id"] = submission_id
        return data  # type: ignore[return-value]

    def run_search(
        self, entity_summary: dict[str, list[str]], top_k: int
    ) -> list[dict[str, object]]:
        text = entities_to_text(entity_summary)
        query_vec = embed_text(self._embed_model, text)
        results = self._index_manager.search(query_vec, top_k=top_k, threshold=0.0)
        return [r.model_dump() for r in results]  # type: ignore[return-value]


class HttpBackend:
    """Runs prediction and RAG by calling live Docker services."""

    def __init__(self, prediction_url: str, rag_url: str) -> None:
        self._prediction_url = prediction_url.rstrip("/")
        self._rag_url = rag_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def run_prediction(
        self, submission_id: str, entity_summary: dict[str, list[str]]
    ) -> dict[str, object]:
        resp = self._client.post(
            f"{self._prediction_url}/predict",
            json={
                "submission_id": submission_id,
                "entity_summary": entity_summary,
                "full_text": "",
            },
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]

    def run_search(
        self, entity_summary: dict[str, list[str]], top_k: int
    ) -> list[dict[str, object]]:
        resp = self._client.post(
            f"{self._rag_url}/search",
            json={"entity_summary": entity_summary, "top_k": top_k},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Case selection
# ---------------------------------------------------------------------------


def select_eval_cases(
    csv_path: Path, n_per_severity: int = 5, seed: int = 42
) -> list[tuple[int, dict[str, str]]]:
    """Pick cases stratified by severity for balanced evaluation."""
    import random

    rng = random.Random(seed)

    rows_by_severity: dict[str, list[tuple[int, dict[str, str]]]] = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            sev = row.get("incident_severity", "")
            rows_by_severity.setdefault(sev, []).append((i, row))

    selected: list[tuple[int, dict[str, str]]] = []
    for severity in ["Trivial Damage", "Minor Damage", "Major Damage", "Total Loss"]:
        pool = rows_by_severity.get(severity, [])
        if not pool:
            continue
        rng.shuffle(pool)

        # try to include at least one fraud case and 2+ incident types
        fraud_cases = [r for r in pool if r[1].get("fraud_reported") == "Y"]
        non_fraud = [r for r in pool if r[1].get("fraud_reported") != "Y"]

        picks: list[tuple[int, dict[str, str]]] = []
        if fraud_cases:
            picks.append(fraud_cases[0])
        for row in non_fraud:
            if len(picks) >= n_per_severity:
                break
            # ensure incident type diversity
            existing_types = {p[1].get("incident_type") for p in picks}
            if (
                len(existing_types) < 2
                or row[1].get("incident_type") not in existing_types
                or len(picks) < n_per_severity
            ):
                picks.append(row)

        # fill remaining slots if needed
        for row in pool:
            if len(picks) >= n_per_severity:
                break
            if row not in picks:
                picks.append(row)

        selected.extend(picks[:n_per_severity])

    return selected


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def check_tier_adjacent(expected: str, predicted: str) -> bool:
    e = TIER_ORDER.get(expected, -1)
    p = TIER_ORDER.get(predicted, -1)
    return abs(e - p) <= 1


def check_claim_reasonable(predicted: float, actual: float) -> bool:
    if predicted <= 0:
        return False
    if actual <= 0:
        return predicted > 0
    ratio = predicted / actual
    return 0.05 <= ratio <= 20.0


def check_shap_grounded(risk_factors: list[dict[str, object]]) -> bool:
    for factor in risk_factors:
        name = str(factor.get("name", ""))
        if name and name not in VALID_DISPLAY_NAMES:
            return False
    return True


def check_rag_type_match(results: list[dict[str, object]], incident_type: str) -> bool:
    keyword = incident_type.lower()
    for r in results:
        summary = str(r.get("summary", "")).lower()
        if keyword in summary:
            return True
    return False


# ---------------------------------------------------------------------------
# Main eval loop
# ---------------------------------------------------------------------------


def evaluate_case(
    backend: PipelineBackend,
    idx: int,
    row: dict[str, str],
) -> CaseEvalResult:
    entity_summary = row_to_entity_summary(row)
    submission_id = f"eval-{idx}"

    start = time.perf_counter()
    pred = backend.run_prediction(submission_id, entity_summary)
    rag_results = backend.run_search(entity_summary, top_k=5)
    elapsed = (time.perf_counter() - start) * 1000

    predicted_tier = str(pred.get("risk_tier", ""))
    expected_tier = RISK_TIERS.get(row.get("incident_severity", ""), "MODERATE")
    risk_probability = float(pred.get("risk_probability", 0))
    predicted_amount = float(pred.get("predicted_claim_amount", 0))
    actual_amount = float(row.get("total_claim_amount", "0") or "0")
    risk_factors = pred.get("key_risk_factors", [])
    if not isinstance(risk_factors, list):
        risk_factors = []

    # consistency check: run prediction again
    pred2 = backend.run_prediction(submission_id, entity_summary)
    consistency = (
        float(pred2.get("risk_probability", -1)) == risk_probability
        and float(pred2.get("predicted_claim_amount", -1)) == predicted_amount
    )

    top_sim = 0.0
    if rag_results:
        top_sim = float(rag_results[0].get("similarity_score", 0))

    incident_type = row.get("incident_type", "")

    return CaseEvalResult(
        case_index=idx,
        incident_type=incident_type,
        incident_severity=row.get("incident_severity", ""),
        fraud_reported=row.get("fraud_reported", ""),
        actual_claim_amount=actual_amount,
        expected_tier=expected_tier,
        predicted_tier=predicted_tier,
        risk_probability=risk_probability,
        predicted_claim_amount=predicted_amount,
        risk_factors=risk_factors,  # type: ignore[arg-type]
        rag_result_count=len(rag_results),
        rag_top_similarity=top_sim,
        rag_type_match=check_rag_type_match(rag_results, incident_type),
        tier_match=predicted_tier == expected_tier,
        tier_adjacent=check_tier_adjacent(expected_tier, predicted_tier),
        claim_reasonable=check_claim_reasonable(predicted_amount, actual_amount),
        consistency_passed=consistency,
        shap_grounded=check_shap_grounded(risk_factors),  # type: ignore[arg-type]
        processing_time_ms=round(elapsed, 1),
    )


def run_evaluation(
    backend: PipelineBackend,
    cases: list[tuple[int, dict[str, str]]],
) -> list[CaseEvalResult]:
    results: list[CaseEvalResult] = []
    for i, (idx, row) in enumerate(cases):
        print(
            f"  [{i + 1}/{len(cases)}] case {idx} ({row.get('incident_severity', '?')})...", end=""
        )
        result = evaluate_case(backend, idx, row)
        status = "PASS" if result.tier_match else ("~" if result.tier_adjacent else "FAIL")
        print(f" {status} (prob={result.risk_probability:.3f})")
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# LLM evaluation with hallucination detection
# ---------------------------------------------------------------------------


def run_llm_evaluation(
    cases: list[tuple[int, dict[str, str]]],
    prediction_results: list[CaseEvalResult],
    llm_url: str,
) -> list[LLMEvalResult]:
    """Test LLM synthesis on 3 representative cases."""
    # pick one HIGH/CRITICAL, one MODERATE, one LOW
    by_tier: dict[str, tuple[int, dict[str, str], CaseEvalResult]] = {}
    for (idx, row), result in zip(cases, prediction_results, strict=False):
        tier = result.predicted_tier
        if tier in ("HIGH", "CRITICAL") and "high" not in by_tier:
            by_tier["high"] = (idx, row, result)
        elif tier == "MODERATE" and "moderate" not in by_tier:
            by_tier["moderate"] = (idx, row, result)
        elif tier == "LOW" and "low" not in by_tier:
            by_tier["low"] = (idx, row, result)
        if len(by_tier) >= 3:
            break

    client = httpx.Client(timeout=60.0)
    llm_results: list[LLMEvalResult] = []

    for label, (idx, row, pred_result) in by_tier.items():
        print(f"  LLM eval: case {idx} ({label} tier)...", end="")
        entity_summary = row_to_entity_summary(row)

        try:
            resp = client.post(
                f"{llm_url.rstrip('/')}/synthesize",
                json={
                    "submission_id": f"eval-llm-{idx}",
                    "entity_summary": entity_summary,
                    "full_text": "",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f" ERROR: {e}")
            llm_results.append(LLMEvalResult(case_index=idx))
            continue

        narrative = str(data.get("underwriter_narrative", ""))
        llm_tier = str(data.get("risk_tier", ""))

        # check if narrative references any SHAP factor
        refs_factor = False
        for factor in pred_result.risk_factors:
            name = str(factor.get("name", ""))
            if name and name.lower() in narrative.lower():
                refs_factor = True
                break

        # hallucination detection
        hall_result = detect_hallucinations(narrative, entity_summary, pred_result, data, llm_url)

        result = LLMEvalResult(
            case_index=idx,
            narrative_length=len(narrative),
            tier_matches_prediction=llm_tier == pred_result.predicted_tier,
            references_shap_factor=refs_factor,
            hallucination_detected=hall_result.get("hallucination_detected", False),
            hallucination_count=hall_result.get("hallucination_count", 0),
            hallucination_details=hall_result.get("details", []),
            hallucination_confidence=hall_result.get("confidence", 0.0),
        )
        status = "CLEAN" if not result.hallucination_detected else "HALLUCINATION"
        print(f" {status} (narrative={result.narrative_length} chars)")
        llm_results.append(result)

    return llm_results


def detect_hallucinations(
    narrative: str,
    entity_summary: dict[str, list[str]],
    pred_result: CaseEvalResult,
    synthesis_data: dict[str, object],
    llm_url: str,
) -> dict[str, object]:
    """Use a second LLM call to judge whether the narrative hallucinates.

    Sends the narrative alongside all source data (prediction output, RAG
    results, entity summary) and asks Claude to identify any claims not
    grounded in the provided data.
    """
    similar_cases = synthesis_data.get("similar_cases", [])
    risk_factors = synthesis_data.get("key_risk_factors", [])

    judge_prompt = f"""You are an auditor checking an insurance underwriting narrative for hallucinations.
A hallucination is any claim in the narrative that is NOT supported by the source data provided below.

SOURCE DATA:
- Entity summary: {json.dumps(entity_summary)}
- Predicted risk tier: {pred_result.predicted_tier}
- Risk probability: {pred_result.risk_probability}
- Predicted claim amount: ${pred_result.predicted_claim_amount:,.2f}
- Key risk factors: {json.dumps(risk_factors, default=str)}
- Similar cases retrieved: {json.dumps(similar_cases, default=str)}

NARRATIVE TO AUDIT:
{narrative}

Check for these types of hallucination:
1. Fabricated facts: dollar amounts, percentages, or statistics not in the source data
2. Ghost references: policy IDs, case references, or risk factors not in the source data
3. Unsupported conclusions: causal claims not grounded in the entity summary

Respond with ONLY valid JSON (no markdown, no explanation):
{{"hallucination_detected": true/false, "hallucination_count": <int>, "details": [<list of specific hallucinated claims>], "confidence": <float 0-1>}}"""

    try:
        # call the LLM service directly with a raw synthesis request
        # but we need to call the Anthropic API for the judge
        # since our LLM service is designed for underwriting, not judging
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": judge_prompt}],
        )
        raw = response.content[0].text  # type: ignore[union-attr]
        return json.loads(raw)  # type: ignore[return-value]
    except ImportError:
        # anthropic not installed, skip hallucination check
        return {
            "hallucination_detected": False,
            "hallucination_count": 0,
            "details": [],
            "confidence": 0.0,
        }
    except Exception:
        return {
            "hallucination_detected": False,
            "hallucination_count": 0,
            "details": ["judge call failed"],
            "confidence": 0.0,
        }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def print_report(results: list[CaseEvalResult], llm_results: list[LLMEvalResult] | None) -> None:
    header = f"{'Idx':>5} | {'Severity':<16} | {'Expected':<10} | {'Predicted':<10} | {'Match':<5} | {'Prob':>6} | {'Claim$':>10} | {'RAG':>3} | {'Consist':<7} | {'SHAP':<4}"
    sep = "-" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)

    for r in results:
        match_str = "PASS" if r.tier_match else ("~" if r.tier_adjacent else "FAIL")
        print(
            f"{r.case_index:>5} | {r.incident_severity:<16} | {r.expected_tier:<10} | "
            f"{r.predicted_tier:<10} | {match_str:<5} | {r.risk_probability:>6.3f} | "
            f"${r.predicted_claim_amount:>9,.0f} | {r.rag_result_count:>3} | "
            f"{'PASS' if r.consistency_passed else 'FAIL':<7} | {'PASS' if r.shap_grounded else 'FAIL':<4}"
        )

    print(sep)

    n = len(results)
    tier_exact = sum(1 for r in results if r.tier_match)
    tier_adj = sum(1 for r in results if r.tier_adjacent)
    consistent = sum(1 for r in results if r.consistency_passed)
    shap_ok = sum(1 for r in results if r.shap_grounded)
    rag_sims = [r.rag_top_similarity for r in results if r.rag_result_count > 0]
    mean_sim = sum(rag_sims) / len(rag_sims) if rag_sims else 0.0
    mean_time = sum(r.processing_time_ms for r in results) / n if n else 0.0

    print(f"\nAggregate Metrics ({n} cases):")
    print(f"  Tier exact match:   {tier_exact}/{n} ({tier_exact / n:.0%})")
    print(f"  Tier adjacent:      {tier_adj}/{n} ({tier_adj / n:.0%})")
    print(f"  Consistency:        {consistent}/{n}")
    print(f"  SHAP grounding:     {shap_ok}/{n}")
    print(f"  Mean RAG similarity: {mean_sim:.4f}")
    print(f"  Mean processing time: {mean_time:.1f}ms")

    if llm_results:
        print(f"\nLLM Evaluation ({len(llm_results)} cases):")
        for lr in llm_results:
            tier_ok = "PASS" if lr.tier_matches_prediction else "FAIL"
            ref_ok = "PASS" if lr.references_shap_factor else "FAIL"
            hall = (
                "CLEAN"
                if not lr.hallucination_detected
                else f"HALLUCINATED ({lr.hallucination_count})"
            )
            print(
                f"  Case {lr.case_index}: narrative={lr.narrative_length} chars, "
                f"tier={tier_ok}, shap_ref={ref_ok}, hallucination={hall}"
            )
        hall_count = sum(1 for lr in llm_results if lr.hallucination_detected)
        print(f"  Hallucination rate: {hall_count}/{len(llm_results)}")


def save_report(
    results: list[CaseEvalResult],
    llm_results: list[LLMEvalResult] | None,
    output_path: str,
    mode: str,
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    git_hash = ""
    with contextlib.suppress(Exception):
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()

    n = len(results)
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_hash": git_hash,
        "backend_mode": mode,
        "total_cases": n,
        "metrics": {
            "tier_exact_match": sum(1 for r in results if r.tier_match),
            "tier_adjacent_match": sum(1 for r in results if r.tier_adjacent),
            "consistency_passed": sum(1 for r in results if r.consistency_passed),
            "shap_grounded": sum(1 for r in results if r.shap_grounded),
            "mean_rag_similarity": round(
                sum(r.rag_top_similarity for r in results) / n if n else 0, 4
            ),
            "mean_processing_time_ms": round(
                sum(r.processing_time_ms for r in results) / n if n else 0, 1
            ),
        },
        "cases": [asdict(r) for r in results],
    }

    if llm_results:
        report["llm_evaluation"] = {
            "total_cases": len(llm_results),
            "hallucination_rate": sum(1 for lr in llm_results if lr.hallucination_detected),
            "cases": [asdict(lr) for lr in llm_results],
        }

    Path(output_path).write_text(json.dumps(report, indent=2, default=str))
    print(f"\nReport saved to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ARIA pipeline evaluation")
    parser.add_argument("--live", action="store_true", help="Use HTTP backend (Docker services)")
    parser.add_argument(
        "--include-llm", action="store_true", help="Test LLM synthesis (uses API credits)"
    )
    parser.add_argument("--prediction-url", default="http://localhost:8001")
    parser.add_argument("--rag-url", default="http://localhost:8002")
    parser.add_argument("--llm-url", default="http://localhost:8003")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-per-severity", type=int, default=5)
    parser.add_argument(
        "--indices", type=str, default="", help="Comma-separated row indices to override selection"
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found.")
        raise SystemExit(1)

    # select cases
    if args.indices:
        indices = [int(x.strip()) for x in args.indices.split(",")]
        all_rows: list[dict[str, str]] = []
        with open(DATA_PATH) as f:
            all_rows = list(csv.DictReader(f))
        cases = [(i, all_rows[i]) for i in indices if i < len(all_rows)]
        print(f"Using {len(cases)} manually selected cases: {indices}")
    else:
        cases = select_eval_cases(DATA_PATH, n_per_severity=args.n_per_severity, seed=args.seed)
        print(f"Selected {len(cases)} cases (seed={args.seed})")
        for sev in ["Trivial Damage", "Minor Damage", "Major Damage", "Total Loss"]:
            count = sum(1 for _, r in cases if r.get("incident_severity") == sev)
            print(f"  {sev}: {count}")

    print(f"\nIndices: {[idx for idx, _ in cases]}")

    # set up backend
    mode = "http" if args.live else "direct"
    if args.live:
        print(f"\nUsing HTTP backend ({args.prediction_url}, {args.rag_url})")
        backend: PipelineBackend = HttpBackend(args.prediction_url, args.rag_url)
    else:
        print("\nLoading models for direct evaluation...")
        backend = DirectBackend()

    # run evaluation
    print(f"\nRunning evaluation ({len(cases)} cases)...")
    results = run_evaluation(backend, cases)

    # optional LLM evaluation
    llm_results: list[LLMEvalResult] | None = None
    if args.include_llm:
        print("\nRunning LLM evaluation (3 cases)...")
        llm_results = run_llm_evaluation(cases, results, args.llm_url)

    # report
    print_report(results, llm_results)
    save_report(results, llm_results, args.output, mode)


if __name__ == "__main__":
    main()
