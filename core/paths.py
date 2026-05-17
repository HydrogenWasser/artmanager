"""Path utilities for Pixel Asset Manager."""

import os
from pathlib import Path
from typing import Optional


class PathHelper:
    """Helper for converting between absolute and relative paths."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()

    def to_absolute(self, relative_path: str) -> str:
        """Convert a relative path to absolute path."""
        if not relative_path:
            return str(self.root_path)
        raw_path = Path(relative_path)
        abs_path = raw_path.resolve() if raw_path.is_absolute() else (self.root_path / raw_path).resolve()
        abs_path.relative_to(self.root_path)
        return str(abs_path)

    def to_relative(self, absolute_path: str) -> str:
        """Convert an absolute path to relative path from root."""
        try:
            abs_path = Path(absolute_path).resolve()
            rel = abs_path.relative_to(self.root_path)
            return str(rel).replace("\\", "/")
        except ValueError:
            return absolute_path

    def ensure_inside_root(self, path: str) -> bool:
        """Check if a path is inside the project root."""
        try:
            Path(path).resolve().relative_to(self.root_path)
            return True
        except ValueError:
            return False

    def get_artmgr_path(self) -> str:
        """Get the .artmgr directory path."""
        return str(self.root_path / ".artmgr")

    def get_db_path(self) -> str:
        """Get the SQLite database path."""
        return str(self.root_path / ".artmgr" / "artdb.sqlite")

    def get_thumbnails_path(self) -> str:
        """Get the thumbnails cache directory path."""
        return str(self.root_path / ".artmgr" / "thumbnails")

    def get_config_path(self) -> str:
        """Get the config JSON path."""
        return str(self.root_path / ".artmgr" / "config.json")

    def get_log_path(self) -> str:
        """Get the log file path."""
        return str(self.root_path / ".artmgr" / "app.log")
