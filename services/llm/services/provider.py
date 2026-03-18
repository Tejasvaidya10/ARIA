from typing import Protocol

import httpx

from services.llm.config import LLMSettings
from services.llm.core.schemas import SynthesisResult


class LLMProvider(Protocol):
    """Interface for LLM providers.

    Both the Anthropic (Claude) and Ollama providers implement this.
    Uses structural subtyping -- any class with a matching synthesize()
    method satisfies the protocol, no inheritance needed.
    """

    async def synthesize(
        self,
        entity_summary: dict[str, list[str]],
        full_text: str,
        http_client: httpx.AsyncClient,
        settings: LLMSettings,
    ) -> SynthesisResult: ...
