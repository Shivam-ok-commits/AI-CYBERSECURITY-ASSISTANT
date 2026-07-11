"""Built-in exporters as a bundled plugin."""
import csv
import json
import io
from typing import Any

from ..base import PluginManifest
from ..types import ExporterPlugin


class BuiltinExporterPlugin(ExporterPlugin):
    manifest = PluginManifest(
        id="builtin-exporters",
        name="Built-in Exporters",
        version="1.0.0",
        plugin_type="exporter",
        description="Core export formats: JSON, CSV, plain text.",
        author="Sentinel Team",
    )

    async def initialize(self) -> None:
        pass

    def supported_formats(self) -> list[str]:
        return ["json", "csv", "txt"]

    def export(self, data: Any, fmt: str) -> bytes:
        if fmt == "json":
            return json.dumps(data, indent=2, default=str).encode("utf-8")
        elif fmt == "csv":
            return self._to_csv(data)
        else:
            text = str(data) if not isinstance(data, str) else data
            return text.encode("utf-8")

    def _to_csv(self, data: Any) -> bytes:
        output = io.StringIO()
        if isinstance(data, list) and data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            writer = csv.writer(output)
            for key, value in data.items():
                writer.writerow([key, value])
        return output.getvalue().encode("utf-8")
