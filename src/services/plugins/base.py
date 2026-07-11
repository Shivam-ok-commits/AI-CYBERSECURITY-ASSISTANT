from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    plugin_type: str  # parser | threat-feed | ai-provider | exporter | detection-pack
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = "MIT"
    min_api_version: str = "1.0.0"
    dependencies: list[str] = field(default_factory=list)
    settings_schema: dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    manifest: PluginManifest
    enabled: bool = True
    config: dict[str, Any] = {}

    @abstractmethod
    async def initialize(self) -> None:
        """Called when plugin is loaded and enabled."""
        ...

    async def shutdown(self) -> None:
        """Called when plugin is disabled or app shuts down."""
        ...

    def get_settings(self) -> dict[str, Any]:
        return self.config

    def update_settings(self, settings: dict[str, Any]) -> None:
        self.config.update(settings)
