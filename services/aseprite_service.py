"""Aseprite integration service."""

import os
import subprocess
import tempfile
from pathlib import Path


class AsepriteService:
    """Handles Aseprite executable path and CLI operations."""

    def __init__(self, database_service):
        self.db = database_service
        self._cache_path: str | None = None

    def set_aseprite_path(self, path: str) -> None:
        """Save Aseprite executable path."""
        self._cache_path = path
        self.db.set_setting("aseprite_path", path)

    def get_aseprite_path(self) -> str:
        """Get Aseprite executable path."""
        if self._cache_path is None:
            self._cache_path = self.db.get_setting("aseprite_path", "")
        return self._cache_path

    def is_available(self) -> bool:
        """Check if Aseprite path is configured and exists."""
        path = self.get_aseprite_path()
        return bool(path) and os.path.isfile(path)

    def open_file(self, file_path: str) -> None:
        """Open file with Aseprite, or fallback to system default."""
        aseprite = self.get_aseprite_path()
        if aseprite and os.path.isfile(aseprite):
            subprocess.Popen([aseprite, file_path])
        else:
            os.startfile(file_path)

    def export_preview_png(self, aseprite_file: str, output_png: str) -> bool:
        """Export first frame of aseprite file to PNG using CLI."""
        aseprite = self.get_aseprite_path()
        if not aseprite or not os.path.isfile(aseprite):
            return False
        if not os.path.exists(aseprite_file):
            return False
        try:
            Path(output_png).parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [aseprite, "-b", aseprite_file, "--save-as", output_png],
                capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0 and os.path.exists(output_png)
        except Exception:
            return False
