"""Tests for ThumbnailService."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from services.thumbnail_service import ThumbnailService


class TestThumbnailService(unittest.TestCase):
    def setUp(self):
        self.mock_project = MagicMock()
        self.mock_project.get_thumbnails_path.return_value = tempfile.mkdtemp()
        self.mock_project.to_absolute_path = lambda x: x
        self.service = ThumbnailService(self.mock_project, thumbnail_size=128)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.mock_project.get_thumbnails_path(), ignore_errors=True)

    def test_generate_image_thumbnail_sync(self):
        # Create a simple test image
        try:
            from PIL import Image
            img_path = os.path.join(tempfile.mkdtemp(), "test.png")
            img = Image.new("RGB", (100, 100), color="red")
            img.save(img_path)

            thumb_path = os.path.join(tempfile.mkdtemp(), "thumb.png")
            result = self.service.generate_image_thumbnail_sync(img_path, thumb_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(thumb_path))

            os.remove(img_path)
            os.remove(thumb_path)
        except ImportError:
            self.skipTest("Pillow not available")

    def test_thumbnail_path_generation(self):
        path = self.service._get_thumbnail_path("test.png")
        self.assertTrue(path.endswith(".png"))
        self.assertTrue(os.path.isabs(path))


if __name__ == "__main__":
    unittest.main()
