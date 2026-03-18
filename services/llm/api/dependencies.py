import httpx
from fastapi import Request

from services.llm.config import LLMSettings
from services.llm.services.provider import LLMProvider


def get_settings(request: Request) -> LLMSettings:
    settings: LLMSettings = request.app.state.settings
    return settings


def get_provider(request: Request) -> LLMProvider:
    provider: LLMProvider = request.app.state.provider
    return provider


def get_http_client(request: Request) -> httpx.AsyncClient:
    client: httpx.AsyncClient = request.app.state.http_client
    return client
