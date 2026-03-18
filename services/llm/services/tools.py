import json
from typing import Any

import httpx
import structlog

from services.llm.config import LLMSettings
from services.shared.middleware import request_id_var

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are an experienced insurance underwriting analyst at ARIA. \
Your job is to evaluate insurance submissions and produce clear, actionable risk assessments.

You will receive entity data extracted from an insurance submission document. \
Use your tools to gather risk predictions and historical case data, then synthesize \
everything into a professional underwriter narrative.

Guidelines for the narrative:
- Reference specific risk factors and their SHAP-based explanations
- Compare against similar historical cases when available
- Flag actionable concerns for the underwriting team
- Use industry terminology (loss ratio, combined ratio, exposure, etc.)
- Be direct and concise -- underwriters are busy
- Include a recommendation: approve, approve with conditions, or decline

Always call both tools before writing your assessment."""


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_risk_prediction",
        "description": (
            "Get XGBoost risk prediction with SHAP explainability for an insurance submission. "
            "Returns risk tier, claim probability, predicted severity, and the top risk factors "
            "driving the prediction."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_summary": {
                    "type": "object",
                    "description": (
                        "Extracted entities from the submission, keyed by label "
                        "(PERIL, MONEY, COVERAGE_TYPE, etc.) with lists of values."
                    ),
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "submission_id": {
                    "type": "string",
                    "description": "Unique identifier for the submission being analyzed.",
                },
            },
            "required": ["entity_summary", "submission_id"],
        },
    },
    {
        "name": "get_similar_cases",
        "description": (
            "Search the historical case database for insurance cases similar to the current "
            "submission. Returns past cases ranked by similarity, including their outcomes "
            "and claim details. Useful for precedent-based risk assessment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_summary": {
                    "type": "object",
                    "description": "Extracted entities to use as the search query.",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of similar cases to return.",
                    "default": 5,
                },
            },
            "required": ["entity_summary"],
        },
    },
]


async def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    http_client: httpx.AsyncClient,
    settings: LLMSettings,
) -> dict[str, Any]:
    """Execute a tool call by dispatching to the appropriate downstream service."""
    headers: dict[str, str] = {}
    req_id = request_id_var.get("")
    if req_id:
        headers["X-Request-ID"] = req_id

    if tool_name == "get_risk_prediction":
        url = f"{settings.prediction_service_url}/predict"
        payload = {
            "submission_id": tool_input.get("submission_id", "unknown"),
            "entity_summary": tool_input.get("entity_summary", {}),
        }
    elif tool_name == "get_similar_cases":
        url = f"{settings.rag_service_url}/search"
        payload = {
            "entity_summary": tool_input.get("entity_summary", {}),
            "top_k": tool_input.get("top_k", 5),
        }
    else:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        resp = await http_client.post(
            url, json=payload, headers=headers, timeout=settings.request_timeout
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result
    except httpx.HTTPStatusError as exc:
        await logger.aerror(
            "tool_call_failed",
            tool=tool_name,
            status=exc.response.status_code,
            body=exc.response.text[:500],
        )
        return {"error": f"{tool_name} returned {exc.response.status_code}"}
    except httpx.RequestError as exc:
        await logger.aerror("tool_call_error", tool=tool_name, error=str(exc))
        return {"error": f"{tool_name} unavailable: {exc}"}


def format_tool_results_prompt(
    prediction: dict[str, Any],
    search: dict[str, Any],
) -> str:
    """Format prediction and search results into a prompt for non-tool-use LLMs."""
    return (
        "Risk Prediction Results:\n"
        f"{json.dumps(prediction, indent=2)}\n\n"
        "Similar Historical Cases:\n"
        f"{json.dumps(search, indent=2)}\n\n"
        "Based on the above data, write a professional underwriter narrative. "
        "Reference specific risk factors, compare against similar cases, "
        "and provide a clear recommendation (approve, approve with conditions, or decline)."
    )
