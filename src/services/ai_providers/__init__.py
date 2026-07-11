from typing import Optional
from .base import AIProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .lmstudio_provider import LMStudioProvider

_registry: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
    "lmstudio": LMStudioProvider,
}

_current_provider: Optional[AIProvider] = None


def get_provider(name: Optional[str] = None) -> AIProvider:
    global _current_provider

    if name is None:
        from src.config import settings
        name = settings.ai_provider or "openai"

    if _current_provider is None or _current_provider.name != name:
        cls = _registry.get(name)
        if not cls:
            raise ValueError(f"Unknown AI provider: {name}. Available: {list(_registry.keys())}")
        _current_provider = cls()
        if not _current_provider.is_available():
            from src.services.ai_chat import FALLBACK_RESPONSES
            from src.services.ai_prompts import get_prompt
            return _current_provider

    return _current_provider


def list_providers() -> list[dict]:
    result = []
    for name, cls in _registry.items():
        instance = cls()
        result.append({
            "name": name,
            "available": instance.is_available(),
            "requires_api_key": instance.requires_api_key,
        })
    return result
