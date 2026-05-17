"""Thumbnail generation and caching service."""

import os
import hashlib
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject
from PySide6.QtGui import QPixmap

from core.constants import (
    FILE_TYPE_IMAGE, FILE_TYPE_GIF, FILE_TYPE_ASEPRITE,
    DEFAULT_THUMBNAIL_SIZE,
)


class ThumbnailSignals(QObject):
    finished = Signal(str, str)  # file_path, thumbnail_path
    error = Signal(str, str)     # file_path, error_message


class ThumbnailWorker(QRunnable):
    """Worker for generating thumbnails in background thread."""

    def __init__(self, file_path: str, output_path: str, size: int, signals: ThumbnailSignals,
                 file_type: str = "", aseprite_service=None):
        super().__init__()
        self.file_path = file_path
        self.output_path = output_path
        self.size = size
        self.signals = signals
        self.file_type = file_type
        self.aseprite_service = aseprite_service

    def run(self):
        try:
            if self.file_type == FILE_TYPE_ASEPRITE:
                if not self.aseprite_service or not self.aseprite_service.export_preview_png(
                    self.file_path, self.output_path
                ):
                    raise RuntimeError("Aseprite preview export failed")
                self.signals.finished.emit(self.file_path, self.output_path)
                return

            from PIL import Image
            img = Image.open(self.file_path)
            # Handle animation by using first frame
            if hasattr(img, 'seek') and img.format == 'GIF':
                img.seek(0)
            # Convert to RGBA for consistent output
            if img.mode in ('RGBA', 'LA', 'P'):
                # Keep alpha for PNG output
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            # Resize with aspect ratio
            img.thumbnail((self.size, self.size), Image.LANCZOS)
            # Save as PNG
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(self.output_path, 'PNG')
            self.signals.finished.emit(self.file_path, self.output_path)
        except Exception as e:
            self.signals.error.emit(self.file_path, str(e))


class ThumbnailService:
    """Manages thumbnail generation and caching."""

    def __init__(self, project_service, thumbnail_size: int = DEFAULT_THUMBNAIL_SIZE,
                 aseprite_service=None):
        self.project_service = project_service
        self.thumbnail_size = thumbnail_size
        self.aseprite_service = aseprite_service
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)
        self.signals = ThumbnailSignals()
        self._pending: set[str] = set()
        self.signals.finished.connect(lambda file_path, _thumb_path: self.mark_done(file_path))
        self.signals.error.connect(lambda file_path, _message: self.mark_done(file_path))

    def set_size(self, size: int):
        self.thumbnail_size = size

    def _get_thumbnail_path(self, relative_file_path: str) -> str:
        """Generate thumbnail path based on file path hash."""
        hash_name = hashlib.sha1(relative_file_path.encode('utf-8')).hexdigest() + '.png'
        thumbs_dir = self.project_service.get_thumbnails_path()
        return str(Path(thumbs_dir) / hash_name)

    def _is_thumbnail_valid(self, file_path: str, thumbnail_path: str) -> bool:
        """Check if thumbnail exists and is up to date."""
        if not os.path.exists(thumbnail_path):
            return False
        if not os.path.exists(file_path):
            return False
        file_mtime = os.path.getmtime(file_path)
        thumb_mtime = os.path.getmtime(thumbnail_path)
        return thumb_mtime >= file_mtime

    def ensure_thumbnail(self, relative_file_path: str, file_type: str) -> str:
        """Get thumbnail path, generating if needed. Returns path or empty string."""
        abs_path = self.project_service.to_absolute_path(relative_file_path)
        if not os.path.exists(abs_path):
            return ""

        thumb_path = self._get_thumbnail_path(relative_file_path)

        if self._is_thumbnail_valid(abs_path, thumb_path):
            return thumb_path

        if file_type == FILE_TYPE_ASEPRITE and not self.aseprite_service:
            return ""

        # Queue generation
        if abs_path not in self._pending:
            self._pending.add(abs_path)
            worker = ThumbnailWorker(
                abs_path,
                thumb_path,
                self.thumbnail_size,
                self.signals,
                file_type=file_type,
                aseprite_service=self.aseprite_service,
            )
            self.thread_pool.start(worker)

        return thumb_path

    def generate_image_thumbnail_sync(self, file_path: str, output_path: str) -> bool:
        """Synchronous thumbnail generation."""
        try:
            from PIL import Image
            img = Image.open(file_path)
            if hasattr(img, 'seek') and img.format == 'GIF':
                img.seek(0)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            img.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.LANCZOS)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'PNG')
            return True
        except Exception:
            return False

    def mark_done(self, file_path: str):
        self._pending.discard(file_path)
