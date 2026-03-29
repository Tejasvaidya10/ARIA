from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from services.llm.config import LLMSettings
from services.llm.services.tools import execute_tool


@pytest.fixture()
def settings() -> LLMSettings:
    return LLMSettings()


async def test_execute_tool_prediction_timeout_returns_fallback(
    monkeypatch: pytest.MonkeyPatch, settings: LLMSettings
) -> None:
    async def instant_sleep(_: float) -> None:
        pass

    monkeypatch.setattr("asyncio.sleep", instant_sleep)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.TimeoutException("timed out")

    result = await execute_tool(
        "get_risk_prediction",
        {"entity_summary": {}, "submission_id": "sub-1"},
        mock_client,
        settings,
    )

    assert result["is_fallback"] is True
    assert result["risk_tier"] == "MODERATE"
    assert result["shap_factors"] == []
    assert mock_client.post.call_count == 3


async def test_execute_tool_rag_503_returns_fallback(
    monkeypatch: pytest.MonkeyPatch, settings: LLMSettings
) -> None:
    async def instant_sleep(_: float) -> None:
        pass

    monkeypatch.setattr("asyncio.sleep", instant_sleep)

    mock_response = MagicMock()
    mock_response.status_code = 503

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.HTTPStatusError(
        "503 Service Unavailable", request=MagicMock(), response=mock_response
    )

    result = await execute_tool(
        "get_similar_cases",
        {"entity_summary": {}},
        mock_client,
        settings,
    )

    assert result["is_fallback"] is True
    assert result["similar_cases"] == []
    assert mock_client.post.call_count == 3


async def test_execute_tool_success_passes_through(settings: LLMSettings) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"risk_tier": "HIGH", "risk_probability": 0.8}

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response

    result = await execute_tool(
        "get_risk_prediction",
        {"entity_summary": {"PERIL": ["fire"]}, "submission_id": "sub-2"},
        mock_client,
        settings,
    )

    assert result["risk_tier"] == "HIGH"
    assert "is_fallback" not in result
    assert mock_client.post.call_count == 1


async def test_execute_tool_404_not_retried(settings: LLMSettings) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=mock_response
    )

    result = await execute_tool(
        "get_risk_prediction",
        {"entity_summary": {}, "submission_id": "sub-3"},
        mock_client,
        settings,
    )

    assert result["is_fallback"] is True
    assert mock_client.post.call_count == 1


async def test_execute_tool_unknown_tool_returns_error(settings: LLMSettings) -> None:
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    result = await execute_tool(
        "nonexistent_tool",
        {},
        mock_client,
        settings,
    )

    assert "error" in result
    assert mock_client.post.call_count == 0
