"""Center panel - Asset grid displaying child nodes and files."""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel, QFrame, QMenu, QMessageBox, QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from core.constants import FILE_TYPE_IMAGE, FILE_TYPE_ASEPRITE, FILE_TYPE_GIF


class AssetCard(QFrame):
    """Card widget for displaying a node or file."""

    def __init__(self, title: str, subtitle: str, card_type: str, item_id: int, parent=None):
        super().__init__(parent)
        self.card_type = card_type  # 'node' or 'file'
        self.item_id = item_id
        self.setObjectName("AssetCard")
        self.setFixedSize(180, 220)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Thumbnail placeholder
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 160)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #1E1E1E; border-radius: 4px; font-size: 48px; color: #6CA0DC;"
        )
        icon = "\U0001F4C1" if card_type == "node" else "\U0001F4C4"
        self.thumb_label.setText(icon)
        layout.addWidget(self.thumb_label)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; color: #E6E6E6;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Subtitle
        self.sub_label = QLabel(subtitle)
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")
        layout.addWidget(self.sub_label)

    def set_thumbnail(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
            self.thumb_label.setText("")
            self.thumb_label.setStyleSheet("background-color: #1E1E1E; border-radius: 4px;")
        else:
            icon = "\U0001F4C1" if self.card_type == "node" else "\U0001F4C4"
            self.thumb_label.setText(icon)
            self.thumb_label.setStyleSheet(
                "background-color: #1E1E1E; border-radius: 4px; font-size: 48px; color: #6CA0DC;"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            parent = self.parent()
            while parent and not isinstance(parent, AssetGridPanel):
                parent = parent.parent()
            if parent:
                parent._on_card_clicked(self.card_type, self.item_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        parent = self.parent()
        while parent and not isinstance(parent, AssetGridPanel):
            parent = parent.parent()
        if parent:
            parent._on_card_double_clicked(self.card_type, self.item_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        parent = self.parent()
        while parent and not isinstance(parent, AssetGridPanel):
            parent = parent.parent()
        if parent:
            parent._on_card_context_menu(self.card_type, self.item_id, event.globalPos())
        event.accept()


class AssetGridPanel(QWidget):
    item_selected = Signal(str, int)  # type, id
    node_double_clicked = Signal(int)
    file_double_clicked = Signal(int)

    def __init__(self, app_context):
        super().__init__()
        self.ctx = app_context
        self._current_node_id: int | None = None
        self._cards: list[AssetCard] = []
        self._thumbnail_cards: dict[str, list[AssetCard]] = {}
        self._thumbnail_signal_source = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        # Empty label
        self.empty_label = QLabel("该节点没有子节点或文件")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #A0A0A0; margin-top: 40px;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

    def clear(self):
        self._clear_grid()
        self._current_node_id = None
        self.empty_label.setVisible(False)

    def _clear_grid(self):
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._cards.clear()
        self._thumbnail_cards.clear()

    def load_node(self, node_id: int):
        self._current_node_id = node_id
        self._clear_grid()
        if not self.ctx.is_project_open():
            return
        self._ensure_thumbnail_signal()

        children = self.ctx.database_service.get_children(node_id)
        files = self.ctx.database_service.get_files_by_node(node_id)

        if not children and not files:
            self.empty_label.setVisible(True)
            self.scroll_area.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.scroll_area.setVisible(True)

        row, col = 0, 0
        max_cols = self._calculate_columns()

        for child in children:
            card = AssetCard(child.name, "", "node", child.id)
            self.grid.addWidget(card, row, col)
            self._cards.append(card)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        for file in files:
            import os
            filename = os.path.basename(file.file_path)
            card = AssetCard(filename, file.file_type, "file", file.id)
            self.grid.addWidget(card, row, col)
            self._cards.append(card)

            # Try to load thumbnail
            self._load_file_thumbnail(card, file)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _load_file_thumbnail(self, card: AssetCard, file):
        if not self.ctx.thumbnail_service:
            return
        thumb_path = self.ctx.thumbnail_service.ensure_thumbnail(
            file.file_path, file.file_type
        )
        if thumb_path and os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            card.set_thumbnail(pixmap)
        elif file.file_type in (FILE_TYPE_IMAGE, FILE_TYPE_GIF, FILE_TYPE_ASEPRITE):
            abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
            self._thumbnail_cards.setdefault(abs_path, []).append(card)

    def _ensure_thumbnail_signal(self):
        if self.ctx.thumbnail_service and self._thumbnail_signal_source is not self.ctx.thumbnail_service:
            self.ctx.thumbnail_service.signals.finished.connect(self._on_thumbnail_ready)
            self._thumbnail_signal_source = self.ctx.thumbnail_service

    def _on_thumbnail_ready(self, file_path: str, thumb_path: str):
        if not self.ctx.is_project_open():
            return
        if os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            for card in self._thumbnail_cards.get(file_path, []):
                card.set_thumbnail(pixmap)

    def refresh(self):
        if self._current_node_id is not None:
            self.load_node(self._current_node_id)

    def _calculate_columns(self) -> int:
        width = self.scroll_area.viewport().width() - 20
        card_width = 180 + 12
        cols = max(1, width // card_width)
        return cols

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_node_id is not None:
            self.load_node(self._current_node_id)

    def _on_card_clicked(self, card_type: str, item_id: int):
        self.item_selected.emit(card_type, item_id)

    def _on_card_double_clicked(self, card_type: str, item_id: int):
        if card_type == "node":
            self.node_double_clicked.emit(item_id)
        elif card_type == "file":
            self.file_double_clicked.emit(item_id)
            self._open_file(item_id)

    def _open_file(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        if not os.path.exists(abs_path):
            QMessageBox.warning(self, "提示", "文件不存在，可能已被移动或删除")
            return
        if file.file_type == FILE_TYPE_ASEPRITE:
            self.ctx.aseprite_service.open_file(abs_path)
        else:
            self.ctx.file_system_service.open_file(abs_path)

    def _on_card_context_menu(self, card_type: str, item_id: int, global_pos):
        menu = QMenu(self)
        if card_type == "node":
            act_open = menu.addAction("进入节点")
            act_rename = menu.addAction("重命名")
            act_delete = menu.addAction("删除节点")
            action = menu.exec(global_pos)
            if action == act_open:
                self.node_double_clicked.emit(item_id)
            elif action == act_rename:
                self._rename_node(item_id)
            elif action == act_delete:
                self._delete_node(item_id)
        elif card_type == "file":
            act_open = menu.addAction("打开")
            act_open_ase = menu.addAction("用 Aseprite 打开")
            act_open_folder = menu.addAction("打开所在文件夹")
            menu.addSeparator()
            act_regen = menu.addAction("重新生成缩略图")
            menu.addSeparator()
            act_remove = menu.addAction("从节点移除")
            act_delete = menu.addAction("删除到回收站")
            action = menu.exec(global_pos)
            if action == act_open:
                self._open_file(item_id)
            elif action == act_open_ase:
                self._open_with_aseprite(item_id)
            elif action == act_open_folder:
                self._open_file_folder(item_id)
            elif action == act_regen:
                self._regenerate_thumbnail(item_id)
            elif action == act_remove:
                self._remove_file(item_id)
            elif action == act_delete:
                self._delete_file(item_id)

    def _rename_node(self, node_id: int):
        from PySide6.QtWidgets import QInputDialog
        node = self.ctx.database_service.get_node(node_id)
        if not node:
            return
        new_name, ok = QInputDialog.getText(self, "重命名节点", "新名称:", text=node.name)
        if ok and new_name.strip():
            new_name = new_name.strip()
            try:
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

    def _delete_node(self, node_id: int):
        msg = QMessageBox(self)
        msg.setWindowTitle("确认删除")
        msg.setText("确定删除该节点及其子节点？")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        check = QCheckBox("同时删除磁盘上的对应文件夹")
        msg.setCheckBox(check)

        reply = msg.exec()
        if reply == QMessageBox.Yes:
            # Delete disk folder if checked
            if check.isChecked():
                node = self.ctx.database_service.get_node(node_id)
                if node and node.folder_path:
                    abs_path = self.ctx.project_service.to_absolute_path(node.folder_path)
                    if os.path.exists(abs_path) and os.path.isdir(abs_path):
                        self.ctx.file_system_service.send_to_trash(abs_path)

            self.ctx.database_service.delete_node(node_id)
            self.refresh()

    def _open_with_aseprite(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        if not os.path.exists(abs_path):
            QMessageBox.warning(self, "提示", "文件不存在")
            return
        if self.ctx.aseprite_service.is_available():
            self.ctx.aseprite_service.open_file(abs_path)
        else:
            QMessageBox.warning(self, "提示", "Aseprite 路径未配置，请在设置中配置")

    def _open_file_folder(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        self.ctx.file_system_service.reveal_in_explorer(abs_path)

    def _regenerate_thumbnail(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        if self.ctx.thumbnail_service:
            abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
            thumb_path = self.ctx.thumbnail_service._get_thumbnail_path(file.file_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            self.ctx.thumbnail_service.ensure_thumbnail(file.file_path, file.file_type)
            self.refresh()

    def _remove_file(self, file_id: int):
        reply = QMessageBox.question(
            self, "确认移除", "确定从当前节点移除该文件引用？\n磁盘文件不会被删除。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.ctx.database_service.delete_file_record(file_id)
            self.refresh()

    def _create_search_card(self, title: str, subtitle: str, card_type: str, item_id: int):
        """Create a card for search results."""
        return AssetCard(title, subtitle, card_type, item_id)

    def _delete_file(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定将文件移动到回收站？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
            if os.path.exists(abs_path):
                self.ctx.file_system_service.send_to_trash(abs_path)
            self.ctx.database_service.delete_file_record(file_id)
            self.refresh()

    def add_files_to_current_node(self):
        """Add files to the currently selected node."""
        if self._current_node_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择一个节点")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "All Files (*);;"
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
            "Aseprite (*.aseprite *.ase)"
        )
        if not files:
            return

        # Get target folder from node
        node = self.ctx.database_service.get_node(self._current_node_id)
        if not node:
            return

        # Determine destination folder: use node's auto-calculated folder_path
        if node.folder_path:
            dst_folder = self.ctx.project_service.to_absolute_path(node.folder_path)
        else:
            # Root node or fallback to project root
            dst_folder = self.ctx.project_service.get_root_path()
        self.ctx.file_system_service.ensure_folder(dst_folder)

        import os
        for src_path in files:
            try:
                # Determine file type
                file_type = self.ctx.file_system_service.detect_file_type(src_path)

                # Always copy to the node's folder
                dst_path = self.ctx.file_system_service.copy_file_to_folder(src_path, dst_folder)
                rel_path = self.ctx.project_service.to_relative_path(dst_path)

                # Get dimensions for images
                width, height = 0, 0
                if file_type in (FILE_TYPE_IMAGE, FILE_TYPE_GIF):
                    width, height = self.ctx.file_system_service.get_image_dimensions(
                        self.ctx.project_service.to_absolute_path(rel_path)
                    )

                file_size = self.ctx.file_system_service.get_file_size(
                    self.ctx.project_service.to_absolute_path(rel_path)
                )

                # Add to database
                self.ctx.database_service.add_file(
                    node_id=self._current_node_id,
                    file_path=rel_path,
                    file_type=file_type,
                    width=width,
                    height=height,
                    file_size=file_size
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加文件失败:\n{src_path}\n{e}")

        self.load_node(self._current_node_id)
