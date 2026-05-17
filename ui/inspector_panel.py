"""Right panel - Inspector for node/file properties."""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QFrame, QScrollArea, QMessageBox, QComboBox,
    QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

from core.constants import ROLE_LABELS, ROLE_OTHER


class InspectorPanel(QWidget):
    file_deleted = Signal()  # Emitted when a file is deleted from inspector

    def __init__(self, app_context):
        super().__init__()
        self.ctx = app_context
        self._current_node_id: int | None = None
        self._current_file_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.main_layout = QVBoxLayout(self.content)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(12)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

        # Default message
        self._show_empty()

    def clear(self):
        self._clear_content()
        self._show_empty()
        self._current_node_id = None
        self._current_file_id = None

    def _clear_content(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3F3F46;")
        return line

    def _make_title_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #E6E6E6;"
        )
        label.setWordWrap(True)
        return label

    def _make_subtitle_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; color: #A0A0A0;")
        label.setWordWrap(True)
        return label

    def _show_empty(self):
        self._clear_content()
        label = QLabel("请选择一个节点或文件")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #A0A0A0; margin-top: 20px;")
        self.main_layout.addWidget(label)

    def show_node(self, node_id: int):
        if not self.ctx.is_project_open():
            return
        node = self.ctx.database_service.get_node(node_id)
        if not node:
            return

        self._current_node_id = node_id
        self._current_file_id = None
        self._clear_content()

        # Title: node name
        self.main_layout.addWidget(self._make_title_label(node.name))

        # Path info (relative folder path)
        if node.folder_path:
            self.main_layout.addWidget(self._make_subtitle_label(node.folder_path))

        self.main_layout.addWidget(self._make_separator())

        # Note section
        note_header = QLabel("备注")
        note_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #E6E6E6;")
        self.main_layout.addWidget(note_header)

        self.note_edit = QTextEdit(node.note or "")
        self.note_edit.setMaximumHeight(120)
        self.note_edit.setPlaceholderText("在此输入备注，点击外部区域自动保存...")
        self.note_edit.installEventFilter(self)
        self.main_layout.addWidget(self.note_edit)

        self.main_layout.addStretch()

    def eventFilter(self, obj, event):
        """Auto-save note when focus leaves the text edit."""
        if obj is self.note_edit and event.type() == event.Type.FocusOut:
            if self._current_node_id is not None:
                self._save_node_note()
        return super().eventFilter(obj, event)

    def show_file(self, file_id: int):
        if not self.ctx.is_project_open():
            return
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return

        self._current_node_id = None
        self._current_file_id = file_id
        self._clear_content()

        filename = os.path.basename(file.file_path)

        # Title: filename
        self.main_layout.addWidget(self._make_title_label(filename))

        # Subtitle: full absolute path
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        self.main_layout.addWidget(self._make_subtitle_label(abs_path))

        self.main_layout.addWidget(self._make_separator())

        # File info form
        info_form = QFormLayout()
        info_form.setSpacing(6)

        # File type
        type_edit = QLineEdit(file.file_type)
        type_edit.setReadOnly(True)
        info_form.addRow("类型:", type_edit)

        # Size
        size_str = self._format_size(file.file_size) if file.file_size else "未知"
        size_edit = QLineEdit(size_str)
        size_edit.setReadOnly(True)
        info_form.addRow("大小:", size_edit)

        # Dimensions
        dim_str = f"{file.width} x {file.height}" if file.width and file.height else "未知"
        dim_edit = QLineEdit(dim_str)
        dim_edit.setReadOnly(True)
        info_form.addRow("尺寸:", dim_edit)

        self.main_layout.addLayout(info_form)

        self.main_layout.addWidget(self._make_separator())

        # Role section
        role_header = QLabel("角色")
        role_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #E6E6E6;")
        self.main_layout.addWidget(role_header)

        self.role_combo = QComboBox()
        from core.constants import ROLE_AI_SOURCE, ROLE_ASEPRITE_SOURCE, ROLE_EXPORT_PNG, ROLE_PREVIEW
        from core.constants import ROLE_SPRITESHEET, ROLE_REFERENCE, ROLE_MASK, ROLE_COLLISION_REF
        from core.constants import ROLE_ANIMATION_FRAME, ROLE_OTHER
        roles = [
            ROLE_AI_SOURCE, ROLE_ASEPRITE_SOURCE, ROLE_EXPORT_PNG, ROLE_PREVIEW,
            ROLE_SPRITESHEET, ROLE_REFERENCE, ROLE_MASK, ROLE_COLLISION_REF,
            ROLE_ANIMATION_FRAME, ROLE_OTHER
        ]
        for r in roles:
            self.role_combo.addItem(ROLE_LABELS.get(r, r), r)
        idx = self.role_combo.findData(file.role)
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)
        else:
            self.role_combo.setCurrentIndex(self.role_combo.findData(ROLE_OTHER))

        role_layout = QHBoxLayout()
        role_layout.addWidget(self.role_combo)
        btn_save_role = QPushButton("保存")
        btn_save_role.setFixedWidth(60)
        btn_save_role.clicked.connect(self._save_file_role)
        role_layout.addWidget(btn_save_role)
        self.main_layout.addLayout(role_layout)

        self.main_layout.addWidget(self._make_separator())

        # Action buttons section
        actions_header = QLabel("操作")
        actions_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #E6E6E6;")
        self.main_layout.addWidget(actions_header)

        btn_open = QPushButton("打开文件")
        btn_open.clicked.connect(lambda: self._open_file(file_id))
        self.main_layout.addWidget(btn_open)

        btn_open_folder = QPushButton("打开所在文件夹")
        btn_open_folder.clicked.connect(lambda: self._open_file_folder(file_id))
        self.main_layout.addWidget(btn_open_folder)

        from core.constants import FILE_TYPE_ASEPRITE
        if file.file_type == FILE_TYPE_ASEPRITE:
            btn_open_ase = QPushButton("用 Aseprite 打开")
            btn_open_ase.clicked.connect(lambda: self._open_with_aseprite(file_id))
            self.main_layout.addWidget(btn_open_ase)

        btn_regen = QPushButton("重新生成缩略图")
        btn_regen.clicked.connect(lambda: self._regenerate_thumbnail(file_id))
        self.main_layout.addWidget(btn_regen)

        self.main_layout.addSpacing(8)

        btn_delete = QPushButton("删除到回收站")
        btn_delete.setStyleSheet("QPushButton { color: #D9534F; }")
        btn_delete.clicked.connect(lambda: self._delete_file(file_id))
        self.main_layout.addWidget(btn_delete)

        self.main_layout.addStretch()

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _save_node_note(self):
        if self._current_node_id is None:
            return
        note = self.note_edit.toPlainText()
        try:
            self.ctx.database_service.update_node(self._current_node_id, note=note)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存备注失败:\n{e}")

    def _save_file_role(self):
        if self._current_file_id is None:
            return
        role = self.role_combo.currentData()
        try:
            self.ctx.database_service.update_file(self._current_file_id, role=role)
            QMessageBox.information(self, "成功", "角色已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{e}")

    def _open_file(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        if not self._check_file_exists(abs_path):
            return
        from core.constants import FILE_TYPE_ASEPRITE
        if file.file_type == FILE_TYPE_ASEPRITE:
            self.ctx.aseprite_service.open_file(abs_path)
        else:
            self.ctx.file_system_service.open_file(abs_path)

    def _open_file_folder(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        self.ctx.file_system_service.reveal_in_explorer(abs_path)

    def _open_with_aseprite(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        abs_path = self.ctx.project_service.to_absolute_path(file.file_path)
        if not self._check_file_exists(abs_path):
            return
        if self.ctx.aseprite_service.is_available():
            self.ctx.aseprite_service.open_file(abs_path)
        else:
            QMessageBox.warning(self, "提示", "Aseprite 路径未配置，请在设置中配置")

    def _regenerate_thumbnail(self, file_id: int):
        file = self.ctx.database_service.get_file(file_id)
        if not file:
            return
        if self.ctx.thumbnail_service:
            thumb_path = self.ctx.thumbnail_service._get_thumbnail_path(file.file_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            self.ctx.thumbnail_service.ensure_thumbnail(file.file_path, file.file_type)
            QMessageBox.information(self, "成功", "缩略图已重新生成")

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
            if self._check_file_exists(abs_path):
                self.ctx.file_system_service.send_to_trash(abs_path)
            self.ctx.database_service.delete_file_record(file_id)
            self.clear()
            self.file_deleted.emit()

    def _check_file_exists(self, abs_path: str) -> bool:
        if not os.path.exists(abs_path):
            QMessageBox.warning(self, "提示", "文件不存在，可能已被移动或删除")
            return False
        return True
