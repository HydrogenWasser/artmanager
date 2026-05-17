"""Tests for SyncService."""

import os
import shutil
import tempfile
import unittest

from services.database_service import DatabaseService
from services.file_system_service import FileSystemService
from services.project_service import ProjectService
from services.sync_service import SyncService


class TestSyncService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project = ProjectService()
        self.project.open_project(self.temp_dir)
        self.db = DatabaseService()
        self.db.connect(self.project.get_db_path())
        self.db.initialize_schema()
        self.root_id = self.db.create_node(None, "Root")
        self.fs = FileSystemService()
        self.sync = SyncService(self.project, self.db, self.fs)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_folder_and_file_from_disk(self):
        folder = os.path.join(self.temp_dir, "Characters", "Alice")
        os.makedirs(folder)
        file_path = os.path.join(folder, "alice.png")
        with open(file_path, "wb") as f:
            f.write(b"not a real png")

        changed = self.sync.sync_from_disk()

        self.assertTrue(changed)
        characters = self.db.get_node_by_folder_path("Characters")
        alice = self.db.get_node_by_folder_path("Characters/Alice")
        self.assertIsNotNone(characters)
        self.assertIsNotNone(alice)
        files = self.db.get_files_by_node(alice.id)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].file_path, "Characters/Alice/alice.png")

    def test_remove_file_and_folder_from_disk(self):
        folder = os.path.join(self.temp_dir, "Props")
        os.makedirs(folder)
        file_path = os.path.join(folder, "key.txt")
        with open(file_path, "w") as f:
            f.write("key")
        self.sync.sync_from_disk()

        os.remove(file_path)
        os.rmdir(folder)
        changed = self.sync.sync_from_disk()

        self.assertTrue(changed)
        self.assertIsNone(self.db.get_node_by_folder_path("Props"))
        self.assertEqual(self.db.get_all_files(), [])


if __name__ == "__main__":
    unittest.main()
