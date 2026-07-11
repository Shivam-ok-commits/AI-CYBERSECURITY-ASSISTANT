from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    name: str = ""
    requires_api_key: bool = True

    @abstractmethod
    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    async def explain(self, context: str, detail: str = "standard") -> str:
        prompt = f"Explain this security event in {detail} detail:\n\n{context}"
        return await self.chat([{"role": "user", "content": prompt}], temperature=0.3)

    async def generate_recommendations(self, context: str) -> str:
        prompt = f"Based on this security analysis, provide remediation recommendations:\n\n{context}"
        return await self.chat([{"role": "user", "content": prompt}])

    async def analyze_timeline(self, events: list[dict]) -> str:
        lines = "\n".join(
            f"[{e.get('timestamp','')}] {e.get('event_type','')} src={e.get('source_ip','')}" for e in events[:50]
        )
        prompt = f"Analyze this security event timeline and identify attack stages:\n{lines}"
        return await self.chat([{"role": "user", "content": prompt}])
