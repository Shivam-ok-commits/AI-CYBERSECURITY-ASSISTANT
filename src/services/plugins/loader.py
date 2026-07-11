import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from src.config import settings as app_settings
from .base import BasePlugin, PluginManifest
from .registry import get_registry
from .types import PLUGIN_TYPE_MAP

logger = logging.getLogger(__name__)


def discover_plugins(plugins_dir: Optional[str] = None) -> list[BasePlugin]:
    """Discover and load plugins from the plugins directory."""
    plugins: list[BasePlugin] = []

    search_dirs = _get_plugin_dirs(plugins_dir)
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue

        for entry in os.listdir(search_dir):
            plugin_path = os.path.join(search_dir, entry)
            if not os.path.isdir(plugin_path):
                continue

            plugin = _load_plugin_from_dir(plugin_path)
            if plugin:
                plugins.append(plugin)

    return plugins


def load_bundled_plugins() -> list[BasePlugin]:
    """Load bundled (built-in) plugins."""
    from .bundled.builtin_parsers import BuiltinParserPlugin
    from .bundled.builtin_exporters import BuiltinExporterPlugin
    return [BuiltinParserPlugin(), BuiltinExporterPlugin()]


def _get_plugin_dirs(override: Optional[str] = None) -> list[str]:
    dirs = []

    # User plugins directory (configurable)
    if override:
        dirs.append(override)
    else:
        user_data = os.environ.get("SENTINEL_PLUGINS_DIR", "")
        if user_data:
            dirs.append(user_data)

    # Project-level plugins directory
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    project_plugins = os.path.join(str(base_dir), "plugins")
    dirs.append(project_plugins)

    return dirs


def _load_plugin_from_dir(plugin_dir: str) -> Optional[BasePlugin]:
    """Load a single plugin from a directory."""
    manifest_path = os.path.join(plugin_dir, "plugin.json")
    if not os.path.isfile(manifest_path):
        logger.debug("No plugin.json found in %s, skipping", plugin_dir)
        return None

    import json
    try:
        with open(manifest_path) as f:
            manifest_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to parse manifest in %s: %s", plugin_dir, e)
        return None

    manifest = PluginManifest(
        id=manifest_data.get("id", os.path.basename(plugin_dir)),
        name=manifest_data.get("name", os.path.basename(plugin_dir)),
        version=manifest_data.get("version", "0.1.0"),
        plugin_type=manifest_data.get("plugin_type", "parser"),
        description=manifest_data.get("description", ""),
        author=manifest_data.get("author", ""),
        homepage=manifest_data.get("homepage", ""),
        license=manifest_data.get("license", "MIT"),
        min_api_version=manifest_data.get("min_api_version", "1.0.0"),
        dependencies=manifest_data.get("dependencies", []),
        settings_schema=manifest_data.get("settings_schema", {}),
    )

    if manifest.plugin_type not in PLUGIN_TYPE_MAP:
        logger.warning("Unknown plugin type '%s' in %s", manifest.plugin_type, plugin_dir)
        return None

    # Try to load module
    main_file = manifest_data.get("main", "main.py")
    main_path = os.path.join(plugin_dir, main_file)
    if not os.path.isfile(main_path):
        logger.warning("Plugin entry point not found: %s", main_path)
        return None

    try:
        module = _import_module(manifest.id, main_path)
        if not hasattr(module, "create_plugin"):
            logger.warning("Plugin %s missing create_plugin() function", manifest.id)
            return None
        plugin = module.create_plugin(manifest)
        plugin.manifest = manifest
        return plugin
    except Exception as e:
        logger.error("Failed to load plugin %s: %s", manifest.id, e)
        return None


def _import_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
