import httpx
from .base import AIProvider
from src.config import settings


class OllamaProvider(AIProvider):
    name = "ollama"
    requires_api_key = False

    def is_available(self) -> bool:
        return bool(settings.ollama_base_url)

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.is_available():
            return ""

        base = settings.ollama_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base}/api/chat",
                json={
                    "model": settings.ollama_model or "llama3.2",
                    "messages": messages,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
