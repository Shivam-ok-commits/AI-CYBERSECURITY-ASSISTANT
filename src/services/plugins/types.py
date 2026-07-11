from abc import abstractmethod
from typing import Any, Optional

from .base import BasePlugin


class ParserPlugin(BasePlugin):
    """Plugin that parses custom log formats."""

    @abstractmethod
    def can_parse(self, filename: str, sample: str) -> float:
        """Return confidence score 0.0-1.0 for whether this plugin can parse the file."""
        ...

    @abstractmethod
    def parse(self, text: str) -> list[dict]:
        """Parse log text into event dicts with keys: line_number, timestamp, source_ip, event_type, severity, raw."""
        ...


class ThreatFeedPlugin(BasePlugin):
    """Plugin that provides threat intelligence data."""

    @abstractmethod
    async def lookup(self, indicator: str) -> Optional[dict]:
        """Look up an indicator (IP, domain, hash) and return reputation data or None."""
        ...

    @abstractmethod
    def supported_types(self) -> list[str]:
        """Return list of indicator types supported: ip, domain, hash, url."""
        ...


class AIProviderPlugin(BasePlugin):
    """Plugin that provides an AI model backend."""

    @abstractmethod
    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Send chat messages to the AI model and return response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and reachable."""
        ...


class ExporterPlugin(BasePlugin):
    """Plugin that exports reports/data to external formats."""

    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Return list of export formats supported (pdf, html, json, csv, etc.)."""
        ...

    @abstractmethod
    def export(self, data: Any, fmt: str) -> bytes:
        """Export data in the given format and return bytes."""
        ...


class DetectionPackPlugin(BasePlugin):
    """Plugin that provides detection rules and signatures."""

    @abstractmethod
    def get_rules(self) -> list[dict]:
        """Return list of detection rules with fields: id, name, type, pattern, severity, description."""
        ...

    @abstractmethod
    def match(self, event: dict) -> list[dict]:
        """Match an event against detection rules and return matched rule info."""
        ...


PLUGIN_TYPE_MAP: dict[str, type[BasePlugin]] = {
    "parser": ParserPlugin,
    "threat-feed": ThreatFeedPlugin,
    "ai-provider": AIProviderPlugin,
    "exporter": ExporterPlugin,
    "detection-pack": DetectionPackPlugin,
}
