"""File system operations service."""

import os
import shutil
import subprocess
from pathlib import Path

from send2trash import send2trash

from core.constants import (
    IMAGE_EXTENSIONS, GIF_EXTENSIONS, ASEPRITE_EXTENSIONS,
    JSON_EXTENSIONS, FILE_TYPE_IMAGE, FILE_TYPE_GIF, FILE_TYPE_ASEPRITE,
    FILE_TYPE_JSON, FILE_TYPE_OTHER, FILE_TYPE_FOLDER,
)


class FileSystemService:
    """Handles physical file operations."""

    def detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension."""
        if not file_path:
            return FILE_TYPE_OTHER
        ext = Path(file_path).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            return FILE_TYPE_IMAGE
        if ext in GIF_EXTENSIONS:
            return FILE_TYPE_GIF
        if ext in ASEPRITE_EXTENSIONS:
            return FILE_TYPE_ASEPRITE
        if ext in JSON_EXTENSIONS:
            return FILE_TYPE_JSON
        return FILE_TYPE_OTHER

    def copy_file_to_folder(self, src_path: str, dst_folder: str) -> str:
        """Copy a file to destination folder, return new path."""
        Path(dst_folder).mkdir(parents=True, exist_ok=True)
        src = Path(src_path)
        dst = Path(dst_folder) / src.name
        # If exists, add number suffix
        counter = 1
        stem = src.stem
        suffix = src.suffix
        while dst.exists():
            dst = Path(dst_folder) / f"{stem}_{counter}{suffix}"
            counter += 1
        shutil.copy2(str(src), str(dst))
        return str(dst)

    def move_file_to_folder(self, src_path: str, dst_folder: str) -> str:
        """Move a file to destination folder, return new path."""
        Path(dst_folder).mkdir(parents=True, exist_ok=True)
        src = Path(src_path)
        dst = Path(dst_folder) / src.name
        counter = 1
        stem = src.stem
        suffix = src.suffix
        while dst.exists():
            dst = Path(dst_folder) / f"{stem}_{counter}{suffix}"
            counter += 1
        shutil.move(str(src), str(dst))
        return str(dst)

    def rename_file(self, file_path: str, new_name: str) -> str:
        """Rename a file, return new path."""
        src = Path(file_path)
        dst = src.parent / new_name
        src.rename(dst)
        return str(dst)

    def send_to_trash(self, file_path: str) -> None:
        """Send file to system trash."""
        if os.path.exists(file_path):
            send2trash(file_path)

    def open_file(self, file_path: str) -> None:
        """Open file with default application."""
        if os.path.exists(file_path):
            os.startfile(file_path)

    def reveal_in_explorer(self, file_path: str) -> None:
        """Open Windows Explorer and select the file."""
        if not os.path.exists(file_path):
            return
        abs_path = str(Path(file_path).resolve())
        if os.path.isdir(abs_path):
            subprocess.Popen(["explorer", abs_path])
        else:
            subprocess.Popen(["explorer", "/select,", abs_path])

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def get_image_dimensions(self, file_path: str):
        """Get image width and height using Pillow if available."""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return img.width, img.height
        except Exception:
            return 0, 0

    def ensure_folder(self, folder_path: str) -> None:
        """Ensure a folder exists, creating it if necessary."""
        Path(folder_path).mkdir(parents=True, exist_ok=True)

    def rename_folder(self, old_path: str, new_path: str) -> None:
        """Rename a folder."""
        src = Path(old_path)
        dst = Path(new_path)
        if src.exists() and src.is_dir():
            src.rename(dst)

    def get_folder_size(self, folder_path: str) -> int:
        """Recursively calculate total size of a folder in bytes."""
        total = 0
        path = Path(folder_path)
        if not path.exists() or not path.is_dir():
            return 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += self.get_folder_size(str(entry.path))
        return total
