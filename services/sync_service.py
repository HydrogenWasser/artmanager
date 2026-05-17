"""Synchronize database records with the real project file system."""

from pathlib import Path

from core.constants import FILE_TYPE_IMAGE, FILE_TYPE_GIF


class SyncService:
    """Keeps asset nodes/files aligned with folders/files on disk."""

    def __init__(self, project_service, database_service, file_system_service):
        self.project_service = project_service
        self.db = database_service
        self.fs = file_system_service

    def sync_from_disk(self) -> bool:
        """Scan the project root and add/remove DB records to match disk state.

        Returns True when the database was changed.
        """
        if not self.project_service.is_project_open():
            return False

        root = Path(self.project_service.get_root_path())
        if not root.exists():
            return False

        changed = False
        root_node = self._get_root_node()
        if root_node is None:
            return False

        folders = self._scan_folders(root)
        files = self._scan_files(root)

        changed = self._remove_missing_files(files) or changed
        changed = self._remove_missing_nodes(folders) or changed
        changed = self._ensure_nodes(folders, root_node.id) or changed
        changed = self._ensure_files(files, root_node.id) or changed
        return changed

    def _get_root_node(self):
        roots = self.db.get_root_nodes()
        return roots[0] if roots else None

    def _scan_folders(self, root: Path) -> set[str]:
        folders: set[str] = set()
        for path in root.rglob("*"):
            if not path.is_dir() or self._is_ignored(path):
                continue
            folders.add(self.project_service.to_relative_path(str(path)))
        return folders

    def _scan_files(self, root: Path) -> set[str]:
        files: set[str] = set()
        for path in root.rglob("*"):
            if not path.is_file() or self._is_ignored(path):
                continue
            files.add(self.project_service.to_relative_path(str(path)))
        return files

    def _is_ignored(self, path: Path) -> bool:
        return ".artmgr" in path.parts or "__pycache__" in path.parts

    def _remove_missing_nodes(self, folders: set[str]) -> bool:
        changed = False
        for node in sorted(self.db.get_all_nodes(), key=lambda n: n.folder_path.count("/"), reverse=True):
            if not node.folder_path:
                continue
            if node.folder_path not in folders:
                self.db.delete_node(node.id)
                changed = True
        return changed

    def _remove_missing_files(self, files: set[str]) -> bool:
        changed = False
        for asset_file in self.db.get_all_files():
            if asset_file.file_path not in files:
                self.db.delete_file_record(asset_file.id)
                changed = True
        return changed

    def _ensure_nodes(self, folders: set[str], root_node_id: int) -> bool:
        changed = False
        for folder_path in sorted(folders, key=lambda p: (p.count("/"), p.lower())):
            if self.db.get_node_by_folder_path(folder_path):
                continue

            path = Path(folder_path)
            parent_folder = "" if str(path.parent) == "." else str(path.parent).replace("\\", "/")
            parent = self.db.get_node_by_folder_path(parent_folder) if parent_folder else self.db.get_node(root_node_id)
            if parent is None:
                continue

            self.db.create_node(parent.id, path.name)
            changed = True
        return changed

    def _ensure_files(self, files: set[str], root_node_id: int) -> bool:
        changed = False
        existing = {asset_file.file_path for asset_file in self.db.get_all_files()}
        for file_path in sorted(files, key=str.lower):
            if file_path in existing:
                continue

            parent_folder = Path(file_path).parent
            parent_folder_path = "" if str(parent_folder) == "." else str(parent_folder).replace("\\", "/")
            node = self.db.get_node_by_folder_path(parent_folder_path) if parent_folder_path else self.db.get_node(root_node_id)
            if node is None:
                continue

            abs_path = self.project_service.to_absolute_path(file_path)
            file_type = self.fs.detect_file_type(abs_path)
            width, height = 0, 0
            if file_type in (FILE_TYPE_IMAGE, FILE_TYPE_GIF):
                width, height = self.fs.get_image_dimensions(abs_path)
            file_size = self.fs.get_file_size(abs_path)

            self.db.add_file(
                node_id=node.id,
                file_path=file_path,
                file_type=file_type,
                width=width,
                height=height,
                file_size=file_size,
            )
            changed = True
        return changed
