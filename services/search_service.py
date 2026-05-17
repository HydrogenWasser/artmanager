"""Search service for nodes and files."""

from typing import List
from dataclasses import dataclass


@dataclass
class SearchResult:
    result_type: str  # 'node' or 'file'
    id: int
    name: str
    path: str
    node_id: int | None = None


class SearchService:
    """Handles search across nodes, files, and tags."""

    def __init__(self, database_service):
        self.db = database_service

    def search(self, query: str) -> List[SearchResult]:
        """Search nodes and files matching the query."""
        if not query or not query.strip():
            return []

        results: List[SearchResult] = []
        q = query.strip()

        # Search nodes
        nodes = self.db.search_nodes(q)
        for node in nodes:
            results.append(SearchResult(
                result_type="node",
                id=node.id,
                name=node.name,
                path=node.folder_path or "",
            ))

        # Search files
        files = self.db.search_files(q)
        for file in files:
            import os
            name = os.path.basename(file.file_path)
            results.append(SearchResult(
                result_type="file",
                id=file.id,
                name=name,
                path=file.file_path,
                node_id=file.node_id,
            ))

        return results
