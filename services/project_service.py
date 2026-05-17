"""Project service for managing project root and .artmgr directory."""

import os
from pathlib import Path
from datetime import datetime

from core.paths import PathHelper


class ProjectService:
    """Handles project opening, .artmgr initialization, and path conversions."""

    def __init__(self):
        self._root_path: str = ""
        self._path_helper: PathHelper | None = None

    def open_project(self, root_path: str) -> None:
        """Open a project directory and initialize .artmgr if needed."""
        self._root_path = str(Path(root_path).resolve())
        self._path_helper = PathHelper(self._root_path)
        self._ensure_artmgr()

    def _ensure_artmgr(self) -> None:
        """Create .artmgr directory and subdirectories if they don't exist."""
        artmgr = Path(self.get_artmgr_path())
        artmgr.mkdir(parents=True, exist_ok=True)
        thumbnails = artmgr / "thumbnails"
        thumbnails.mkdir(exist_ok=True)

    def is_project_open(self) -> bool:
        """Check if a project is currently open."""
        return bool(self._root_path) and self._path_helper is not None

    def get_root_path(self) -> str:
        """Get the project root path."""
        return self._root_path

    def get_artmgr_path(self) -> str:
        """Get the .artmgr directory path."""
        if self._path_helper:
            return self._path_helper.get_artmgr_path()
        return ""

    def get_db_path(self) -> str:
        """Get the SQLite database path."""
        if self._path_helper:
            return self._path_helper.get_db_path()
        return ""

    def get_thumbnails_path(self) -> str:
        """Get the thumbnails cache directory path."""
        if self._path_helper:
            return self._path_helper.get_thumbnails_path()
        return ""

    def get_log_path(self) -> str:
        """Get the log file path."""
        if self._path_helper:
            return self._path_helper.get_log_path()
        return ""

    def to_absolute_path(self, relative_path: str) -> str:
        """Convert relative path to absolute path."""
        if self._path_helper:
            return self._path_helper.to_absolute(relative_path)
        return relative_path

    def to_relative_path(self, absolute_path: str) -> str:
        """Convert absolute path to relative path."""
        if self._path_helper:
            return self._path_helper.to_relative(absolute_path)
        return absolute_path

    def path_helper(self) -> PathHelper | None:
        """Get the path helper instance."""
        return self._path_helper
