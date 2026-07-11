"""Built-in parsers as a bundled plugin."""
from ..base import BasePlugin, PluginManifest
from ..types import ParserPlugin


class BuiltinParserPlugin(ParserPlugin):
    manifest = PluginManifest(
        id="builtin-parsers",
        name="Built-in Parsers",
        version="1.0.0",
        plugin_type="parser",
        description="Core log parsers for syslog, Apache, Nginx, Windows EVTX, and generic formats.",
        author="Sentinel Team",
    )

    async def initialize(self) -> None:
        pass

    def can_parse(self, filename: str, sample: str) -> float:
        from src.services.log_parser import detect_source_type
        source = detect_source_type(sample, filename)
        return 0.9 if source != "generic" else 0.5

    def parse(self, text: str) -> list[dict]:
        from src.services.log_parser import parse_log
        return parse_log(text, "auto")
