import json
import logging
from pathlib import Path
from typing import Any, Optional

from src.database import get_db
from .base import BasePlugin, PluginManifest
from .types import PLUGIN_TYPE_MAP

logger = logging.getLogger(__name__)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._db_initialized = False

    def init_db(self) -> None:
        if self._db_initialized:
            return
        with get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    plugin_type TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    author TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    config TEXT NOT NULL DEFAULT '{}',
                    installed_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
        self._db_initialized = True

    def register(self, plugin: BasePlugin) -> None:
        self._plugins[plugin.manifest.id] = plugin
        self._persist(plugin)
        logger.info("Plugin registered: %s v%s (%s)", plugin.manifest.name, plugin.manifest.version, plugin.manifest.plugin_type)

    def unregister(self, plugin_id: str) -> None:
        plugin = self._plugins.pop(plugin_id, None)
        if plugin:
            logger.info("Plugin unregistered: %s", plugin_id)

    def get(self, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(plugin_id)

    def list(self, plugin_type: Optional[str] = None) -> list[dict]:
        result = []
        for p in self._plugins.values():
            if plugin_type and p.manifest.plugin_type != plugin_type:
                continue
            result.append(self._serialize(p))
        return result

    def enable(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        plugin.enabled = True
        with get_db() as conn:
            conn.execute("UPDATE plugins SET enabled = 1 WHERE id = ?", (plugin_id,))
        logger.info("Plugin enabled: %s", plugin_id)
        return True

    def disable(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        plugin.enabled = False
        with get_db() as conn:
            conn.execute("UPDATE plugins SET enabled = 0 WHERE id = ?", (plugin_id,))
        logger.info("Plugin disabled: %s", plugin_id)
        return True

    def update_config(self, plugin_id: str, config: dict[str, Any]) -> bool:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        plugin.update_settings(config)
        with get_db() as conn:
            conn.execute("UPDATE plugins SET config = ? WHERE id = ?", (json.dumps(config), plugin_id))
        return True

    def load_persisted_state(self) -> None:
        self.init_db()
        with get_db() as conn:
            rows = conn.execute("SELECT id, enabled, config FROM plugins").fetchall()
        for row in rows:
            plugin = self._plugins.get(row["id"])
            if plugin:
                plugin.enabled = bool(row["enabled"])
                try:
                    plugin.config = json.loads(row["config"]) if row["config"] else {}
                except (json.JSONDecodeError, TypeError):
                    plugin.config = {}

    def _persist(self, plugin: BasePlugin) -> None:
        self.init_db()
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO plugins (id, name, version, plugin_type, description, author, enabled, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plugin.manifest.id,
                plugin.manifest.name,
                plugin.manifest.version,
                plugin.manifest.plugin_type,
                plugin.manifest.description,
                plugin.manifest.author,
                1 if plugin.enabled else 0,
                json.dumps(plugin.config),
            ))

    def _serialize(self, plugin: BasePlugin) -> dict:
        return {
            "id": plugin.manifest.id,
            "name": plugin.manifest.name,
            "version": plugin.manifest.version,
            "plugin_type": plugin.manifest.plugin_type,
            "description": plugin.manifest.description,
            "author": plugin.manifest.author,
            "enabled": plugin.enabled,
            "config": plugin.config,
            "settings_schema": plugin.manifest.settings_schema,
        }


_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.init_db()
    return _registry
