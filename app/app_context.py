"""Application context - central service container."""

from services.project_service import ProjectService
from services.database_service import DatabaseService
from services.file_system_service import FileSystemService
from services.thumbnail_service import ThumbnailService
from services.aseprite_service import AsepriteService
from services.search_service import SearchService
from services.settings_service import SettingsService
from services.sync_service import SyncService
from services.file_watcher_service import FileWatcherService


class AppContext:
    """Holds all service instances and provides centralized access."""

    def __init__(self):
        self.project_service = ProjectService()
        self.database_service = DatabaseService()
        self.file_system_service = FileSystemService()
        self.thumbnail_service: ThumbnailService | None = None
        self.aseprite_service: AsepriteService | None = None
        self.search_service: SearchService | None = None
        self.settings_service: SettingsService | None = None
        self.sync_service: SyncService | None = None
        self.file_watcher_service = FileWatcherService()

    def open_project(self, root_path: str) -> None:
        """Open a project and initialize all services."""
        self.file_watcher_service.stop()
        if self.database_service:
            self.database_service.close()

        self.project_service.open_project(root_path)
        db_path = self.project_service.get_db_path()
        self.database_service.connect(db_path)
        self.database_service.initialize_schema()
        created_default_tree = self.database_service.create_default_tree_if_empty()
        if created_default_tree:
            for node in self.database_service.get_all_nodes():
                if node.folder_path:
                    self.file_system_service.ensure_folder(
                        self.project_service.to_absolute_path(node.folder_path)
                    )

        self.aseprite_service = AsepriteService(self.database_service)
        self.thumbnail_service = ThumbnailService(self.project_service, aseprite_service=self.aseprite_service)
        self.search_service = SearchService(self.database_service)
        self.settings_service = SettingsService(self.database_service)
        self.sync_service = SyncService(
            self.project_service,
            self.database_service,
            self.file_system_service,
        )
        self.sync_service.sync_from_disk()
        self.file_watcher_service.start(self.project_service.get_root_path())

        # Load settings
        thumb_size = self.settings_service.get_thumbnail_size()
        if self.thumbnail_service:
            self.thumbnail_service.set_size(thumb_size)

    def is_project_open(self) -> bool:
        return self.project_service.is_project_open()

    def close(self) -> None:
        """Clean up resources."""
        self.file_watcher_service.stop()
        if self.database_service:
            self.database_service.close()
