import httpx
from .base import AIProvider
from src.config import settings


class AnthropicProvider(AIProvider):
    name = "anthropic"
    requires_api_key = True

    def is_available(self) -> bool:
        return bool(settings.anthropic_api_key)

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        if not self.is_available():
            return ""

        system = ""
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                contents.append({"role": msg["role"], "content": msg["content"]})

        if not contents:
            contents.append({"role": "user", "content": "Hello"})

        body: dict = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": contents,
            "temperature": temperature,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
