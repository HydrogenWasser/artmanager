"""Core data models for Pixel Asset Manager."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AssetNode:
    id: int
    parent_id: Optional[int]
    name: str
    type: str = ""  # Deprecated: kept for DB compatibility
    folder_path: str = ""
    sort_order: int = 0
    note: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AssetFile:
    id: int
    node_id: int
    file_path: str
    file_type: str
    role: str
    thumbnail_path: str
    file_hash: str
    width: int
    height: int
    frame_count: int
    file_size: int
    created_at: str
    updated_at: str


@dataclass
class Tag:
    id: int
    name: str
    color: str
    created_at: str
