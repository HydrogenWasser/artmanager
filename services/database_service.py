"""Database service for SQLite operations."""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Any

from core.models import AssetNode, AssetFile, Tag



class DatabaseService:
    """Handles all database operations."""

    def __init__(self):
        self._db_path: str = ""
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self, db_path: str) -> None:
        """Connect to SQLite database."""
        self._db_path = db_path
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # Enable foreign keys
        self._conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def initialize_schema(self) -> None:
        """Initialize database schema from schema.sql."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        schema_path = Path(__file__).parent.parent / "data" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = f.read()
        self._conn.executescript(schema)
        self._conn.commit()

    def create_default_tree_if_empty(self) -> bool:
        """Create default asset tree if no nodes exist."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        cursor = self._conn.execute("SELECT COUNT(*) FROM asset_nodes")
        count = cursor.fetchone()[0]
        if count > 0:
            return False

        now = datetime.now().isoformat()
        # Create root node (folder_path = "" means project root)
        cursor = self._conn.execute(
            """INSERT INTO asset_nodes (parent_id, name, type, folder_path, sort_order, note, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (None, "美术资源", "root", "", 0, "", now, now)
        )
        root_id = cursor.lastrowid

        # Create default categories under root
        categories = ["角色", "场景", "道具", "UI", "参考图", "未分类"]
        for i, name in enumerate(categories):
            self._conn.execute(
                """INSERT INTO asset_nodes (parent_id, name, type, folder_path, sort_order, note, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (root_id, name, "", name, i, "", now, now)
            )
        self._conn.commit()
        return True

    # --- AssetNode CRUD ---

    def create_node(self, parent_id: Optional[int], name: str,
                    sort_order: int = 0, note: str = "") -> int:
        # Auto-calculate folder_path based on parent
        folder_path = ""
        if parent_id is not None:
            parent = self.get_node(parent_id)
            if parent:
                if parent.folder_path:
                    folder_path = f"{parent.folder_path}/{name}"
                else:
                    folder_path = name
        now = datetime.now().isoformat()
        cursor = self._conn.execute(
            """INSERT INTO asset_nodes (parent_id, name, type, folder_path, sort_order, note, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (parent_id, name, "", folder_path, sort_order, note, now, now)
        )
        self._conn.commit()
        return cursor.lastrowid

    def update_node(self, node_id: int, **kwargs) -> None:
        allowed = {"name", "parent_id", "folder_path", "sort_order", "note"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [node_id]
        self._conn.execute(
            f"UPDATE asset_nodes SET {set_clause} WHERE id = ?", values
        )
        self._conn.commit()

    def rename_node(self, node_id: int, new_name: str) -> str:
        """Rename a node and update descendant folder/file paths.

        Returns the node's previous folder_path so callers can synchronize the
        corresponding disk folder before or after the database update.
        """
        node = self.get_node(node_id)
        if not node:
            raise ValueError(f"Node not found: {node_id}")

        old_folder_path = node.folder_path
        if node.parent_id is None:
            new_folder_path = ""
        else:
            parent = self.get_node(node.parent_id)
            if parent and parent.folder_path:
                new_folder_path = f"{parent.folder_path}/{new_name}"
            else:
                new_folder_path = new_name

        now = datetime.now().isoformat()
        with self._conn:
            self._conn.execute(
                "UPDATE asset_nodes SET name = ?, folder_path = ?, updated_at = ? WHERE id = ?",
                (new_name, new_folder_path, now, node_id),
            )
            self._update_children_folder_paths(node_id, new_folder_path, commit=False)
            self._update_file_path_prefix(old_folder_path, new_folder_path)
        return old_folder_path

    def can_move_node(self, node_id: int, new_parent_id: Optional[int]) -> bool:
        """Check if moving node under new_parent would create a cycle or move root."""
        node = self.get_node(node_id)
        if not node:
            return False
        # Cannot move root node (parent_id is None)
        if node.parent_id is None:
            return False
        # Cannot move to itself
        if node_id == new_parent_id:
            return False
        # Cannot move under its own descendants
        current = new_parent_id
        while current is not None:
            parent = self.get_node(current)
            if parent is None:
                break
            if parent.parent_id == node_id:
                return False
            current = parent.parent_id
        return True

    def move_node(self, node_id: int, new_parent_id: Optional[int]) -> None:
        """Move node to a new parent and recalculate folder_path for itself and all descendants."""
        node = self.get_node(node_id)
        if not node:
            return
        old_folder_path = node.folder_path

        # Calculate new folder_path based on new parent
        new_folder_path = ""
        if new_parent_id is not None:
            parent = self.get_node(new_parent_id)
            if parent:
                if parent.folder_path:
                    new_folder_path = f"{parent.folder_path}/{node.name}"
                else:
                    new_folder_path = node.name
        else:
            new_folder_path = node.name

        now = datetime.now().isoformat()
        with self._conn:
            self._conn.execute(
                "UPDATE asset_nodes SET parent_id = ?, folder_path = ?, updated_at = ? WHERE id = ?",
                (new_parent_id, new_folder_path, now, node_id),
            )
            self._update_children_folder_paths(node_id, new_folder_path, commit=False)
            self._update_file_path_prefix(old_folder_path, new_folder_path)

    def _update_children_folder_paths(self, parent_id: int, parent_folder_path: str, commit: bool = True) -> None:
        """Recursively update folder_path for all descendants."""
        children = self.get_children(parent_id)
        for child in children:
            old_path = child.folder_path
            if parent_folder_path:
                new_path = f"{parent_folder_path}/{child.name}"
            else:
                new_path = child.name
            now = datetime.now().isoformat()
            self._conn.execute(
                "UPDATE asset_nodes SET folder_path = ?, updated_at = ? WHERE id = ?",
                (new_path, now, child.id),
            )
            self._update_file_path_prefix(old_path, new_path)
            self._update_children_folder_paths(child.id, new_path, commit=False)
        if commit:
            self._conn.commit()

    def _update_file_path_prefix(self, old_prefix: str, new_prefix: str) -> None:
        """Update asset file paths when a node folder moves."""
        if old_prefix == new_prefix:
            return

        rows = self._conn.execute("SELECT id, file_path FROM asset_files").fetchall()
        now = datetime.now().isoformat()
        for row in rows:
            file_path = row["file_path"]
            new_file_path = None

            if old_prefix:
                if file_path == old_prefix:
                    new_file_path = new_prefix
                elif file_path.startswith(old_prefix + "/"):
                    suffix = file_path[len(old_prefix):]
                    new_file_path = f"{new_prefix}{suffix}" if new_prefix else suffix.lstrip("/")
            elif new_prefix:
                new_file_path = f"{new_prefix}/{file_path}" if file_path else new_prefix

            if new_file_path is not None and new_file_path != file_path:
                self._conn.execute(
                    "UPDATE asset_files SET file_path = ?, updated_at = ? WHERE id = ?",
                    (new_file_path, now, row["id"]),
                )

    def delete_node(self, node_id: int) -> None:
        self._conn.execute("DELETE FROM asset_nodes WHERE id = ?", (node_id,))
        self._conn.commit()

    def get_node(self, node_id: int) -> Optional[AssetNode]:
        row = self._conn.execute(
            "SELECT * FROM asset_nodes WHERE id = ?", (node_id,)
        ).fetchone()
        if row:
            return AssetNode(**dict(row))
        return None

    def get_children(self, parent_id: Optional[int]) -> List[AssetNode]:
        if parent_id is None:
            rows = self._conn.execute(
                "SELECT * FROM asset_nodes WHERE parent_id IS NULL ORDER BY sort_order, name"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM asset_nodes WHERE parent_id = ? ORDER BY sort_order, name",
                (parent_id,)
            ).fetchall()
        return [AssetNode(**dict(r)) for r in rows]

    def get_root_nodes(self) -> List[AssetNode]:
        return self.get_children(None)

    def get_all_nodes(self) -> List[AssetNode]:
        rows = self._conn.execute(
            "SELECT * FROM asset_nodes ORDER BY sort_order, name"
        ).fetchall()
        return [AssetNode(**dict(r)) for r in rows]

    def get_node_by_folder_path(self, folder_path: str) -> Optional[AssetNode]:
        row = self._conn.execute(
            "SELECT * FROM asset_nodes WHERE folder_path = ? ORDER BY id LIMIT 1",
            (folder_path,)
        ).fetchone()
        if row:
            return AssetNode(**dict(row))
        return None

    # --- AssetFile CRUD ---

    def add_file(self, node_id: int, file_path: str, file_type: str,
                 role: str = "", thumbnail_path: str = "", file_hash: str = "",
                 width: int = 0, height: int = 0, frame_count: int = 0,
                 file_size: int = 0) -> int:
        now = datetime.now().isoformat()
        cursor = self._conn.execute(
            """INSERT INTO asset_files
               (node_id, file_path, file_type, role, thumbnail_path, file_hash,
                width, height, frame_count, file_size, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (node_id, file_path, file_type, role, thumbnail_path, file_hash,
             width, height, frame_count, file_size, now, now)
        )
        self._conn.commit()
        return cursor.lastrowid

    def update_file(self, file_id: int, **kwargs) -> None:
        allowed = {"file_path", "file_type", "role", "thumbnail_path",
                   "file_hash", "width", "height", "frame_count", "file_size"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [file_id]
        self._conn.execute(
            f"UPDATE asset_files SET {set_clause} WHERE id = ?", values
        )
        self._conn.commit()

    def delete_file_record(self, file_id: int) -> None:
        self._conn.execute("DELETE FROM asset_files WHERE id = ?", (file_id,))
        self._conn.commit()

    def get_file(self, file_id: int) -> Optional[AssetFile]:
        row = self._conn.execute(
            "SELECT * FROM asset_files WHERE id = ?", (file_id,)
        ).fetchone()
        if row:
            return AssetFile(**dict(row))
        return None

    def get_files_by_node(self, node_id: int) -> List[AssetFile]:
        rows = self._conn.execute(
            "SELECT * FROM asset_files WHERE node_id = ? ORDER BY file_path",
            (node_id,)
        ).fetchall()
        return [AssetFile(**dict(r)) for r in rows]

    def get_all_files(self) -> List[AssetFile]:
        rows = self._conn.execute(
            "SELECT * FROM asset_files ORDER BY file_path"
        ).fetchall()
        return [AssetFile(**dict(r)) for r in rows]

    # --- Tags ---

    def create_tag(self, name: str, color: str = "#888888") -> int:
        now = datetime.now().isoformat()
        cursor = self._conn.execute(
            "INSERT OR IGNORE INTO tags (name, color, created_at) VALUES (?, ?, ?)",
            (name, color, now)
        )
        self._conn.commit()
        if cursor.lastrowid:
            return cursor.lastrowid
        row = self._conn.execute(
            "SELECT id FROM tags WHERE name = ?", (name,)
        ).fetchone()
        return row["id"] if row else 0

    def get_all_tags(self) -> List[Tag]:
        rows = self._conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [Tag(**dict(r)) for r in rows]

    def get_tags_for_node(self, node_id: int) -> List[Tag]:
        rows = self._conn.execute(
            """SELECT t.* FROM tags t
               JOIN asset_node_tags ant ON t.id = ant.tag_id
               WHERE ant.node_id = ? ORDER BY t.name""",
            (node_id,)
        ).fetchall()
        return [Tag(**dict(r)) for r in rows]

    def add_tag_to_node(self, node_id: int, tag_id: int) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO asset_node_tags (node_id, tag_id) VALUES (?, ?)",
            (node_id, tag_id)
        )
        self._conn.commit()

    def remove_tag_from_node(self, node_id: int, tag_id: int) -> None:
        self._conn.execute(
            "DELETE FROM asset_node_tags WHERE node_id = ? AND tag_id = ?",
            (node_id, tag_id)
        )
        self._conn.commit()

    # --- Settings ---

    def get_setting(self, key: str, default: str = "") -> str:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self._conn.commit()

    # --- Search ---

    def search_nodes(self, query: str) -> List[AssetNode]:
        like = f"%{query}%"
        rows = self._conn.execute(
            """SELECT * FROM asset_nodes
               WHERE name LIKE ? OR note LIKE ?
               ORDER BY name""",
            (like, like)
        ).fetchall()
        return [AssetNode(**dict(r)) for r in rows]

    def search_files(self, query: str) -> List[AssetFile]:
        like = f"%{query}%"
        rows = self._conn.execute(
            """SELECT * FROM asset_files
               WHERE file_path LIKE ? OR role LIKE ?
               ORDER BY file_path""",
            (like, like)
        ).fetchall()
        return [AssetFile(**dict(r)) for r in rows]
