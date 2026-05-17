"""Tests for FileSystemService."""

import os
import tempfile
import unittest

from services.file_system_service import FileSystemService
from core.constants import FILE_TYPE_IMAGE, FILE_TYPE_ASEPRITE, FILE_TYPE_JSON, FILE_TYPE_OTHER


class TestFileSystemService(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystemService()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_file_type(self):
        self.assertEqual(self.fs.detect_file_type("test.png"), FILE_TYPE_IMAGE)
        self.assertEqual(self.fs.detect_file_type("test.jpg"), FILE_TYPE_IMAGE)
        self.assertEqual(self.fs.detect_file_type("test.jpeg"), FILE_TYPE_IMAGE)
        self.assertEqual(self.fs.detect_file_type("test.webp"), FILE_TYPE_IMAGE)
        self.assertEqual(self.fs.detect_file_type("test.aseprite"), FILE_TYPE_ASEPRITE)
        self.assertEqual(self.fs.detect_file_type("test.ase"), FILE_TYPE_ASEPRITE)
        self.assertEqual(self.fs.detect_file_type("test.json"), FILE_TYPE_JSON)
        self.assertEqual(self.fs.detect_file_type("test.txt"), FILE_TYPE_OTHER)

    def test_copy_file(self):
        src = os.path.join(self.temp_dir, "source.txt")
        with open(src, "w") as f:
            f.write("hello")
        dst_folder = os.path.join(self.temp_dir, "dest")
        dst = self.fs.copy_file_to_folder(src, dst_folder)
        self.assertTrue(os.path.exists(dst))
        with open(dst) as f:
            self.assertEqual(f.read(), "hello")

    def test_rename_file(self):
        src = os.path.join(self.temp_dir, "old.txt")
        with open(src, "w") as f:
            f.write("test")
        dst = self.fs.rename_file(src, "new.txt")
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.exists(src))

    def test_get_file_size(self):
        path = os.path.join(self.temp_dir, "test.txt")
        with open(path, "w") as f:
            f.write("hello")
        size = self.fs.get_file_size(path)
        self.assertEqual(size, 5)


if __name__ == "__main__":
    unittest.main()
