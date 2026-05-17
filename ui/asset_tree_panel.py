"""Left panel - Asset tree widget with drag-and-drop support."""

import os
import shutil

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMenu, QMessageBox, QInputDialog, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer


class AssetTreeWidget(QTreeWidget):
    """Tree widget that lets Qt draw drag indicators and delegates drop logic."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def startDrag(self, supported_actions):
        item = self.currentItem()
        self.owner._drag_source_node_id = item.data(0, Qt.UserRole) if item else None
        super().startDrag(supported_actions)

    def dropEvent(self, event):
        self.owner.dropEvent(event)
        event.accept()


class AssetTreePanel(QWidget):
    node_selected = Signal(int)

    def __init__(self, app_context):
        super().__init__()
        self.ctx = app_context
        self._drag_source_node_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = AssetTreeWidget(self)
        self.tree.setHeaderLabel("资源树")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Enable drag-and-drop
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeWidget.DragDrop)
        self.tree.setDefaultDropAction(Qt.MoveAction)

        layout.addWidget(self.tree)

    def refresh(self, extra_expand_ids: set[int] | None = None, selected_node_id: int | None = None):
        """Reload tree from database."""
        expanded_ids = self._get_expanded_node_ids()
        if extra_expand_ids:
            expanded_ids.update(node_id for node_id in extra_expand_ids if node_id is not None)
        current_node_id = selected_node_id if selected_node_id is not None else self.get_current_node_id()

        self.tree.blockSignals(True)
        self.tree.clear()
        if not self.ctx.is_project_open():
            self.tree.blockSignals(False)
            return

        root_nodes = self.ctx.database_service.get_root_nodes()
        for node in root_nodes:
            item = self._build_tree_item(node)
            self.tree.addTopLevelItem(item)
            self._load_children(item, node.id)
            item.setExpanded(node.id in expanded_ids or node.parent_id is None)

        self._restore_expanded_node_ids(expanded_ids)
        if current_node_id is not None:
            item = self._find_item_by_id(self.tree.invisibleRootItem(), current_node_id)
            if item:
                self._expand_item_ancestors(item)
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
        self.tree.blockSignals(False)

    def _get_expanded_node_ids(self) -> set[int]:
        expanded: set[int] = set()

        def collect(parent: QTreeWidgetItem):
            for i in range(parent.childCount()):
                child = parent.child(i)
                node_id = child.data(0, Qt.UserRole)
                if child.isExpanded() and node_id is not None:
                    expanded.add(node_id)
                collect(child)

        collect(self.tree.invisibleRootItem())
        return expanded

    def _restore_expanded_node_ids(self, expanded_ids: set[int]) -> None:
        for node_id in expanded_ids:
            item = self._find_item_by_id(self.tree.invisibleRootItem(), node_id)
            if item:
                self._expand_item_ancestors(item)
                item.setExpanded(True)

    def _expand_item_ancestors(self, item: QTreeWidgetItem) -> None:
        parent = item.parent()
        while parent:
            parent.setExpanded(True)
            parent = parent.parent()

    def _build_tree_item(self, node) -> QTreeWidgetItem:
        item = QTreeWidgetItem([node.name])
        item.setData(0, Qt.UserRole, node.id)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        return item

    def _load_children(self, parent_item: QTreeWidgetItem, parent_id: int):
        children = self.ctx.database_service.get_children(parent_id)
        for child in children:
            child_item = self._build_tree_item(child)
            parent_item.addChild(child_item)
            self._load_children(child_item, child.id)

    def get_current_node_id(self) -> int | None:
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return None

    def select_node(self, node_id: int):
        """Select and expand a node by id."""
        item = self._find_item_by_id(self.tree.invisibleRootItem(), node_id)
        if item:
            self._expand_item_ancestors(item)
            self.tree.setCurrentItem(item)
            item.setExpanded(True)
            # Scroll to item
            self.tree.scrollToItem(item)

    def _find_item_by_id(self, parent: QTreeWidgetItem, node_id: int) -> QTreeWidgetItem | None:
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == node_id:
                return child
            result = self._find_item_by_id(child, node_id)
            if result:
                return result
        return None

    def _on_selection_changed(self):
        node_id = self.get_current_node_id()
        if node_id is not None:
            self.node_selected.emit(node_id)

    def _on_item_double_clicked(self, item, column):
        node_id = item.data(0, Qt.UserRole)
        if node_id is not None:
            self.node_selected.emit(node_id)

    # --- Drag and Drop ---

    def dragEnterEvent(self, event):
        if event.source() == self.tree:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() == self.tree:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        try:
            if event.source() != self.tree:
                event.ignore()
                return

            source_id = self._drag_source_node_id
            if source_id is None:
                source_item = self.tree.currentItem()
                source_id = source_item.data(0, Qt.UserRole) if source_item else None
            if source_id is None:
                event.ignore()
                return

            target_item = self.tree.itemAt(event.position().toPoint())
            if not target_item:
                event.ignore()
                return

            new_parent_id = target_item.data(0, Qt.UserRole)

            if source_id == new_parent_id:
                event.ignore()
                return

            if not self.ctx.database_service.can_move_node(source_id, new_parent_id):
                QMessageBox.warning(self, "提示", "不能将节点移动到自身或其子节点下，也不能移动根节点")
                event.ignore()
                return

            node = self.ctx.database_service.get_node(source_id)
            if not node:
                event.ignore()
                return

            parent = self.ctx.database_service.get_node(new_parent_id)
            new_folder_path = f"{parent.folder_path}/{node.name}" if parent and parent.folder_path else node.name

            old_abs = self.ctx.project_service.to_absolute_path(node.folder_path) if node.folder_path else ""
            new_abs = self.ctx.project_service.to_absolute_path(new_folder_path)

            if old_abs and os.path.exists(old_abs):
                if os.path.exists(new_abs):
                    QMessageBox.warning(self, "提示", f"目标位置已存在同名文件夹：{new_folder_path}")
                    event.ignore()
                    return

                size = self.ctx.file_system_service.get_folder_size(old_abs)
                SIZE_LIMIT = 100 * 1024 * 1024
                if size > SIZE_LIMIT:
                    mb = size / (1024 * 1024)
                    reply = QMessageBox.question(
                        self, "确认移动",
                        f"该文件夹大小为 {mb:.1f} MB，超过 100 MB。\n确定要移动吗？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        event.ignore()
                        return

                try:
                    parent_dir = os.path.dirname(new_abs)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                    shutil.move(old_abs, new_abs)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"移动磁盘文件夹失败：\n{e}")
                    event.ignore()
                    return

            try:
                self.ctx.database_service.move_node(source_id, new_parent_id)
            except Exception as e:
                if old_abs and os.path.exists(new_abs) and not os.path.exists(old_abs):
                    try:
                        old_parent = os.path.dirname(old_abs)
                        if old_parent:
                            os.makedirs(old_parent, exist_ok=True)
                        shutil.move(new_abs, old_abs)
                    except Exception:
                        pass
                QMessageBox.critical(self, "错误", f"移动节点失败：\n{e}")
                event.ignore()
                return

            event.accept()
            QTimer.singleShot(0, lambda node_id=source_id: self._refresh_after_move(node_id))
        finally:
            self._drag_source_node_id = None

    def _refresh_after_move(self, node_id: int) -> None:
        node = self.ctx.database_service.get_node(node_id)
        if not node:
            self.refresh()
            return

        expand_ids = {node_id}
        parent_id = node.parent_id
        while parent_id is not None:
            expand_ids.add(parent_id)
            parent = self.ctx.database_service.get_node(parent_id)
            parent_id = parent.parent_id if parent else None

        self.refresh(extra_expand_ids=expand_ids, selected_node_id=node_id)
        self.node_selected.emit(node_id)

    # --- Context Menu ---

    def _on_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        node_id = item.data(0, Qt.UserRole)
        self.tree.setCurrentItem(item)

        menu = QMenu(self)
        act_new = menu.addAction("新建子节点")
        act_rename = menu.addAction("重命名")
        act_delete = menu.addAction("删除节点")
        menu.addSeparator()
        act_open_folder = menu.addAction("打开文件夹")

        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        if action == act_new:
            self._action_new_child(node_id)
        elif action == act_rename:
            self._action_rename(item, node_id)
        elif action == act_delete:
            self._action_delete(item, node_id)
        elif action == act_open_folder:
            self._action_open_folder(node_id)

    def _action_new_child(self, parent_id: int):
        from ui.dialogs import NewNodeDialog
        dialog = NewNodeDialog(self)
        if dialog.exec():
            name = dialog.get_data()
            try:
                new_id = self.ctx.database_service.create_node(
                    parent_id=parent_id,
                    name=name
                )
                # Auto-create the corresponding folder on disk
                node = self.ctx.database_service.get_node(new_id)
                if node and node.folder_path:
                    abs_folder = self.ctx.project_service.to_absolute_path(node.folder_path)
                    self.ctx.file_system_service.ensure_folder(abs_folder)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建节点失败:\n{e}")

    def _action_rename(self, item: QTreeWidgetItem, node_id: int):
        current_text = item.text(0)
        new_name, ok = QInputDialog.getText(self, "重命名节点", "新名称:", text=current_text)
        if ok and new_name.strip():
            new_name = new_name.strip()
            try:
                node = self.ctx.database_service.get_node(node_id)
                if not node:
                    return

                old_abs = self.ctx.project_service.to_absolute_path(node.folder_path) if node.folder_path else ""
                if node.parent_id is None:
                    new_folder_path = ""
                else:
                    parent = self.ctx.database_service.get_node(node.parent_id)
                    new_folder_path = f"{parent.folder_path}/{new_name}" if parent and parent.folder_path else new_name
                new_abs = self.ctx.project_service.to_absolute_path(new_folder_path) if new_folder_path else ""

                moved_folder = False
                if old_abs and os.path.isdir(old_abs) and old_abs != new_abs:
                    if os.path.exists(new_abs):
                        QMessageBox.warning(self, "提示", "目标位置已存在同名文件夹")
                        return
                    parent_dir = os.path.dirname(new_abs)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                    self.ctx.file_system_service.rename_folder(old_abs, new_abs)
                    moved_folder = True

                try:
                    self.ctx.database_service.rename_node(node_id, new_name)
                except Exception:
                    if moved_folder and os.path.exists(new_abs) and not os.path.exists(old_abs):
                        self.ctx.file_system_service.rename_folder(new_abs, old_abs)
                    raise
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败:\n{e}")

    def _action_delete(self, item: QTreeWidgetItem, node_id: int):
        msg = QMessageBox(self)
        msg.setWindowTitle("确认删除")
        msg.setText("确定要删除该节点吗？")
        msg.setInformativeText("该节点下的子节点也会被删除。")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        check = QCheckBox("同时删除磁盘上的对应文件夹")
        msg.setCheckBox(check)

        reply = msg.exec()
        if reply == QMessageBox.Yes:
            try:
                # Delete disk folder if checked
                if check.isChecked():
                    node = self.ctx.database_service.get_node(node_id)
                    if node and node.folder_path:
                        abs_path = self.ctx.project_service.to_absolute_path(node.folder_path)
                        if os.path.exists(abs_path) and os.path.isdir(abs_path):
                            self.ctx.file_system_service.send_to_trash(abs_path)

                self.ctx.database_service.delete_node(node_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败:\n{e}")

    def _action_open_folder(self, node_id: int):
        import subprocess
        node = self.ctx.database_service.get_node(node_id)
        if not node:
            return
        if node.folder_path:
            abs_path = self.ctx.project_service.to_absolute_path(node.folder_path)
            if os.path.isdir(abs_path):
                subprocess.Popen(["explorer", abs_path])
            else:
                QMessageBox.warning(self, "提示", "文件夹不存在")
        else:
            # Root node or nodes without folder_path - open project root
            abs_path = self.ctx.project_service.get_root_path()
            subprocess.Popen(["explorer", abs_path])
