import httpx
from .base import AIProvider
from src.config import settings


class LMStudioProvider(AIProvider):
    name = "lmstudio"
    requires_api_key = False

    def is_available(self) -> bool:
        return bool(settings.lmstudio_base_url)

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.is_available():
            return ""

        base = settings.lmstudio_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base}/v1/chat/completions",
                json={
                    "model": settings.lmstudio_model or "local-model",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
