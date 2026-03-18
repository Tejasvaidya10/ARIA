from services.llm.config import LLMSettings
from services.llm.services.anthropic_provider import AnthropicProvider
from services.llm.services.ollama_provider import OllamaProvider
from services.llm.services.provider import LLMProvider


def get_provider(settings: LLMSettings) -> LLMProvider:
    """Create the appropriate LLM provider based on config.

    Set LLM_PROVIDER=anthropic for Claude (production) or
    LLM_PROVIDER=ollama for local development.
    """
    if settings.provider == "anthropic":
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
