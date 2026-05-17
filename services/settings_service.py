"""Settings service for application configuration."""

import json
from typing import Any

from core.constants import DEFAULT_THUMBNAIL_SIZE


class SettingsService:
    """Manages application settings stored in SQLite."""

    def __init__(self, database_service):
        self.db = database_service

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        value = self.db.get_setting(key, "")
        if value == "":
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        if not isinstance(value, str):
            value = json.dumps(value)
        self.db.set_setting(key, value)

    def get_aseprite_path(self) -> str:
        return self.get("aseprite_path", "")

    def set_aseprite_path(self, path: str) -> None:
        self.set("aseprite_path", path)

    def get_thumbnail_size(self) -> int:
        return self.get("thumbnail_size", DEFAULT_THUMBNAIL_SIZE)

    def set_thumbnail_size(self, size: int) -> None:
        self.set("thumbnail_size", size)

    def get_theme(self) -> str:
        return self.get("theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)

    def get_last_opened_node(self) -> int | None:
        val = self.get("last_opened_node")
        return int(val) if val is not None else None

    def set_last_opened_node(self, node_id: int) -> None:
        self.set("last_opened_node", node_id)
