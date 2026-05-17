"""Dialogs for Pixel Asset Manager."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QMessageBox, QFileDialog,
    QGroupBox, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt

from core.constants import THUMBNAIL_SIZES, DEFAULT_THUMBNAIL_SIZE


class NewNodeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建节点")
        self.setMinimumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _on_ok(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入节点名称")
            return
        self.accept()

    def get_data(self):
        return self.name_edit.text().strip()


class SettingsDialog(QDialog):
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.ctx = app_context
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # General settings group
        general_group = QGroupBox("常规")
        general_form = QFormLayout(general_group)

        # Aseprite path
        ase_layout = QHBoxLayout()
        self.ase_edit = QLineEdit()
        self.ase_edit.setPlaceholderText("Aseprite.exe 路径")
        ase_layout.addWidget(self.ase_edit)
        btn_browse_ase = QPushButton("浏览...")
        btn_browse_ase.clicked.connect(self._browse_aseprite)
        ase_layout.addWidget(btn_browse_ase)
        general_form.addRow("Aseprite 路径:", ase_layout)

        # Thumbnail size
        self.thumb_combo = QComboBox()
        for size in THUMBNAIL_SIZES:
            self.thumb_combo.addItem(f"{size}x{size}", size)
        general_form.addRow("缩略图尺寸:", self.thumb_combo)

        layout.addWidget(general_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _browse_aseprite(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Aseprite", "", "Executable (*.exe);;All Files (*)"
        )
        if path:
            self.ase_edit.setText(path)

    def _load_settings(self):
        if not self.ctx.is_project_open():
            return
        ase_path = self.ctx.settings_service.get_aseprite_path()
        self.ase_edit.setText(ase_path)
        thumb_size = self.ctx.settings_service.get_thumbnail_size()
        idx = self.thumb_combo.findData(thumb_size)
        if idx >= 0:
            self.thumb_combo.setCurrentIndex(idx)

    def _on_ok(self):
        if self.ctx.is_project_open():
            self.ctx.settings_service.set_aseprite_path(self.ase_edit.text().strip())
            self.ctx.settings_service.set_thumbnail_size(self.thumb_combo.currentData())
            # Update thumbnail service
            if self.ctx.thumbnail_service:
                self.ctx.thumbnail_service.set_size(self.thumb_combo.currentData())
        self.accept()

    def get_data(self):
        return {
            "aseprite_path": self.ase_edit.text().strip(),
            "thumbnail_size": self.thumb_combo.currentData(),
        }
