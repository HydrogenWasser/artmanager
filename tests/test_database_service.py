"""Tests for DatabaseService."""

import os
import tempfile
import unittest

from services.database_service import DatabaseService


class TestDatabaseService(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseService()
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db.connect(self.db_path)
        self.db.initialize_schema()

    def tearDown(self):
        self.db.close()
        os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_create_node(self):
        node_id = self.db.create_node(None, "TestNode")
        self.assertIsNotNone(node_id)
        node = self.db.get_node(node_id)
        self.assertEqual(node.name, "TestNode")

    def test_create_node_with_parent(self):
        root_id = self.db.create_node(None, "Root")
        child_id = self.db.create_node(root_id, "Child")
        child = self.db.get_node(child_id)
        self.assertEqual(child.folder_path, "Child")

    def test_update_node(self):
        node_id = self.db.create_node(None, "OldName")
        self.db.update_node(node_id, name="NewName")
        node = self.db.get_node(node_id)
        self.assertEqual(node.name, "NewName")

    def test_delete_node(self):
        node_id = self.db.create_node(None, "ToDelete")
        self.db.delete_node(node_id)
        node = self.db.get_node(node_id)
        self.assertIsNone(node)

    def test_default_tree(self):
        self.db.create_default_tree_if_empty()
        roots = self.db.get_root_nodes()
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].name, "美术资源")
        children = self.db.get_children(roots[0].id)
        self.assertTrue(len(children) >= 5)

    def test_add_file(self):
        node_id = self.db.create_node(None, "TestNode")
        file_id = self.db.add_file(node_id, "test.png", "image")
        self.assertIsNotNone(file_id)
        files = self.db.get_files_by_node(node_id)
        self.assertEqual(len(files), 1)

    def test_search_nodes(self):
        self.db.create_node(None, "Alice")
        results = self.db.search_nodes("Alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alice")

    def test_move_node_updates_descendant_file_paths(self):
        root_id = self.db.create_node(None, "Root")
        characters_id = self.db.create_node(root_id, "Characters")
        props_id = self.db.create_node(root_id, "Props")
        alice_id = self.db.create_node(characters_id, "Alice")
        file_id = self.db.add_file(alice_id, "Characters/Alice/alice.png", "image")

        self.db.move_node(alice_id, props_id)

        moved = self.db.get_node(alice_id)
        file = self.db.get_file(file_id)
        self.assertEqual(moved.folder_path, "Props/Alice")
        self.assertEqual(file.file_path, "Props/Alice/alice.png")

    def test_rename_node_updates_descendant_and_file_paths(self):
        root_id = self.db.create_node(None, "Root")
        parent_id = self.db.create_node(root_id, "Characters")
        child_id = self.db.create_node(parent_id, "Idle")
        file_id = self.db.add_file(child_id, "Characters/Idle/frame.png", "image")

        old_path = self.db.rename_node(parent_id, "Actors")

        parent = self.db.get_node(parent_id)
        child = self.db.get_node(child_id)
        file = self.db.get_file(file_id)
        self.assertEqual(old_path, "Characters")
        self.assertEqual(parent.folder_path, "Actors")
        self.assertEqual(child.folder_path, "Actors/Idle")
        self.assertEqual(file.file_path, "Actors/Idle/frame.png")


if __name__ == "__main__":
    unittest.main()
