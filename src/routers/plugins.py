from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.services.auth import get_current_user
from src.services.plugins import get_registry, discover_plugins, load_bundled_plugins

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/")
def list_plugins(
    plugin_type: str = Query("", alias="type"),
    user: dict = Depends(get_current_user),
):
    registry = get_registry()
    return registry.list(plugin_type=plugin_type or None)


@router.get("/{plugin_id}")
def get_plugin(plugin_id: str, user: dict = Depends(get_current_user)):
    registry = get_registry()
    plugin = registry.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")
    return registry._serialize(plugin)


@router.post("/{plugin_id}/enable")
def enable_plugin(plugin_id: str, user: dict = Depends(get_current_user)):
    registry = get_registry()
    if not registry.enable(plugin_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")
    return {"status": "enabled", "id": plugin_id}


@router.post("/{plugin_id}/disable")
def disable_plugin(plugin_id: str, user: dict = Depends(get_current_user)):
    registry = get_registry()
    if not registry.disable(plugin_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")
    return {"status": "disabled", "id": plugin_id}


@router.put("/{plugin_id}/config")
def update_plugin_config(plugin_id: str, body: dict, user: dict = Depends(get_current_user)):
    registry = get_registry()
    if not registry.update_config(plugin_id, body.get("config", {})):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")
    return {"status": "updated", "id": plugin_id}


@router.post("/discover")
def discover_new_plugins(
    plugins_dir: str = Query("", alias="dir"),
    user: dict = Depends(get_current_user),
):
    registry = get_registry()
    discovered = discover_plugins(plugins_dir or None)
    count = 0
    for plugin in discovered:
        if not registry.get(plugin.manifest.id):
            registry.register(plugin)
            count += 1
    return {"discovered": count, "total": len(discovered)}


@router.post("/reload")
def reload_bundled_plugins(user: dict = Depends(get_current_user)):
    registry = get_registry()
    bundled = load_bundled_plugins()
    count = 0
    for plugin in bundled:
        existing = registry.get(plugin.manifest.id)
        if not existing:
            registry.register(plugin)
            count += 1
    return {"loaded": count}
