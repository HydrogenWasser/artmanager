"""Main window for Pixel Asset Manager."""

import json
import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QToolBar,
    QStatusBar, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QToolButton, QMenu
)
from PySide6.QtCore import Qt, QTimer, QSettings

from ui.asset_tree_panel import AssetTreePanel
from ui.asset_grid_panel import AssetGridPanel
from ui.inspector_panel import InspectorPanel
from ui.dialogs import NewNodeDialog, SettingsDialog


class MainWindow(QMainWindow):
    MAX_RECENT_PROJECTS = 5

    def __init__(self, app_context):
        super().__init__()
        self.ctx = app_context
        self.setWindowTitle("美术资源管理工具")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 900)
        self.showMaximized()

        self._settings = QSettings("PixelAssetManager", "App")
        self._recent_menu = None

        self._setup_ui()
        self._connect_signals()

        # Prompt to open project on startup (delayed so window shows first)
        QTimer.singleShot(100, self._prompt_open_project)

    # --- Settings helpers ---

    def _get_recent_projects(self) -> list[str]:
        raw = self._settings.value("recent_projects", "")
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def _add_recent_project(self, path: str) -> None:
        recent = self._get_recent_projects()
        # Remove if already exists, then insert at front
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:self.MAX_RECENT_PROJECTS]
        self._settings.setValue("recent_projects", json.dumps(recent))
        self._settings.setValue("last_project", path)
        self._update_recent_menu()

    def _get_last_project(self) -> str:
        return self._settings.value("last_project", "")

    def _set_last_project(self, path: str) -> None:
        self._settings.setValue("last_project", path)

    # --- UI ---

    def _setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Project menu button
        btn_project = QToolButton()
        btn_project.setText("项目")
        btn_project.setPopupMode(QToolButton.InstantPopup)

        project_menu = QMenu(btn_project)
        act_new = project_menu.addAction("新建项目")
        act_new.triggered.connect(self._on_new_project)
        act_open = project_menu.addAction("打开项目")
        act_open.triggered.connect(self._on_open_project)
        project_menu.addSeparator()
        self._recent_menu = project_menu.addMenu("最近项目")
        self._update_recent_menu()

        btn_project.setMenu(project_menu)
        self.toolbar.addWidget(btn_project)

        btn_new_node = QPushButton("新建节点")
        btn_new_node.setFlat(True)
        btn_new_node.clicked.connect(self._on_new_node)
        self.toolbar.addWidget(btn_new_node)

        btn_add_file = QPushButton("添加文件")
        btn_add_file.setFlat(True)
        btn_add_file.clicked.connect(self._on_add_file)
        self.toolbar.addWidget(btn_add_file)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setFlat(True)
        btn_refresh.clicked.connect(self._on_refresh)
        self.toolbar.addWidget(btn_refresh)

        self.toolbar.addSeparator()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索资源...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.setClearButtonEnabled(True)
        self.toolbar.addWidget(self.search_edit)

        self.toolbar.addSeparator()

        btn_settings = QPushButton("设置")
        btn_settings.setFlat(True)
        btn_settings.clicked.connect(self._on_settings)
        self.toolbar.addWidget(btn_settings)

        # Splitter with three panels
        self.splitter = QSplitter(Qt.Horizontal)

        self.tree_panel = AssetTreePanel(self.ctx)
        self.tree_panel.setMinimumWidth(200)
        self.tree_panel.setMaximumWidth(350)

        self.grid_panel = AssetGridPanel(self.ctx)
        self.grid_panel.setMinimumWidth(400)

        self.inspector_panel = InspectorPanel(self.ctx)
        self.inspector_panel.setMinimumWidth(250)
        self.inspector_panel.setMaximumWidth(350)

        self.splitter.addWidget(self.tree_panel)
        self.splitter.addWidget(self.grid_panel)
        self.splitter.addWidget(self.inspector_panel)
        self.splitter.setSizes([250, 750, 250])

        layout.addWidget(self.splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _update_recent_menu(self):
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        recent = self._get_recent_projects()
        if not recent:
            act_none = self._recent_menu.addAction("(无)")
            act_none.setEnabled(False)
        else:
            for path in recent:
                if os.path.exists(path):
                    act = self._recent_menu.addAction(path)
                    act.triggered.connect(lambda checked=False, p=path: self._open_project_path(p))

    def _connect_signals(self):
        self.tree_panel.node_selected.connect(self._on_node_selected)
        self.grid_panel.item_selected.connect(self._on_grid_item_selected)
        self.grid_panel.node_double_clicked.connect(self._on_node_double_clicked)
        self.inspector_panel.file_deleted.connect(self.grid_panel.refresh)
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.ctx.file_watcher_service.changed.connect(self._on_file_system_changed)

    def _prompt_open_project(self):
        if self.ctx.is_project_open():
            return
        last = self._get_last_project()
        if last and os.path.isdir(last):
            self._open_project_path(last)
            return
        reply = QMessageBox.question(
            self,
            "打开项目",
            "是否选择一个美术资源根目录？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._on_open_project()

    def _on_new_project(self):
        folder = QFileDialog.getExistingDirectory(self, "选择项目根目录（新建）")
        if not folder:
            return
        self._open_project_path(folder)

    def _on_open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "选择美术资源根目录")
        if not folder:
            return
        self._open_project_path(folder)

    def _open_project_path(self, folder: str):
        try:
            self.ctx.open_project(folder)
            self._add_recent_project(folder)
            self.setWindowTitle(f"美术资源管理工具 - {folder}")
            self.status_bar.showMessage(f"已打开项目: {folder}")
            self.tree_panel.refresh()
            self.grid_panel.clear()
            self.inspector_panel.clear()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开项目失败:\n{e}")

    def _on_new_node(self):
        if not self.ctx.is_project_open():
            QMessageBox.warning(self, "提示", "请先打开一个项目")
            return
        current_node_id = self.tree_panel.get_current_node_id()
        if current_node_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择一个父节点")
            return
        dialog = NewNodeDialog(self)
        if dialog.exec():
            name = dialog.get_data()
            try:
                new_id = self.ctx.database_service.create_node(
                    parent_id=current_node_id,
                    name=name
                )
                # Auto-create the corresponding folder on disk
                node = self.ctx.database_service.get_node(new_id)
                if node and node.folder_path:
                    abs_folder = self.ctx.project_service.to_absolute_path(node.folder_path)
                    self.ctx.file_system_service.ensure_folder(abs_folder)
                self.tree_panel.refresh()
                self.status_bar.showMessage(f"创建节点: {name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建节点失败:\n{e}")

    def _on_add_file(self):
        if not self.ctx.is_project_open():
            QMessageBox.warning(self, "提示", "请先打开一个项目")
            return
        self.grid_panel.add_files_to_current_node()
        node_id = self.tree_panel.get_current_node_id()
        if node_id is not None:
            self._update_status_bar(node_id)

    def _on_refresh(self):
        if not self.ctx.is_project_open():
            return
        if self.ctx.sync_service:
            self.ctx.sync_service.sync_from_disk()
        self.tree_panel.refresh()
        self.grid_panel.refresh()
        self.status_bar.showMessage("已刷新")

    def _on_file_system_changed(self):
        if not self.ctx.is_project_open() or not self.ctx.sync_service:
            return
        if not self.ctx.sync_service.sync_from_disk():
            return

        current_node_id = self.tree_panel.get_current_node_id()
        self.tree_panel.refresh(selected_node_id=current_node_id)
        self.grid_panel.refresh()
        if current_node_id is not None and self.ctx.database_service.get_node(current_node_id):
            self.inspector_panel.show_node(current_node_id)
            self._update_status_bar(current_node_id)
        else:
            self.inspector_panel.clear()
            self.status_bar.showMessage("文件系统已同步")

    def _on_settings(self):
        if not self.ctx.is_project_open():
            QMessageBox.warning(self, "提示", "请先打开一个项目")
            return
        dialog = SettingsDialog(self.ctx, self)
        dialog.exec()

    def _on_node_selected(self, node_id: int):
        self.grid_panel.load_node(node_id)
        self.inspector_panel.show_node(node_id)
        self._update_status_bar(node_id)

    def _on_grid_item_selected(self, item_type: str, item_id: int):
        if item_type == "node":
            self.inspector_panel.show_node(item_id)
        elif item_type == "file":
            self.inspector_panel.show_file(item_id)

    def _on_node_double_clicked(self, node_id: int):
        self.tree_panel.select_node(node_id)

    def _on_search_changed(self, text: str):
        if not self.ctx.is_project_open():
            return
        text = text.strip()
        if not text:
            # Restore current node view
            node_id = self.tree_panel.get_current_node_id()
            if node_id is not None:
                self.grid_panel.load_node(node_id)
            return

        # Perform search
        results = self.ctx.search_service.search(text)
        if not results:
            self.grid_panel._clear_grid()
            self.grid_panel.empty_label.setText("未找到匹配结果")
            self.grid_panel.empty_label.setVisible(True)
            self.grid_panel.scroll_area.setVisible(False)
            return

        # Display search results in grid
        self.grid_panel._clear_grid()
        self.grid_panel.empty_label.setVisible(False)
        self.grid_panel.scroll_area.setVisible(True)

        row, col = 0, 0
        max_cols = self.grid_panel._calculate_columns()

        for result in results:
            if result.result_type == "node":
                card = self.grid_panel._create_search_card(result.name, "", "node", result.id)
            else:
                card = self.grid_panel._create_search_card(result.name, result.path, "file", result.id)

            self.grid_panel.grid.addWidget(card, row, col)
            self.grid_panel._cards.append(card)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _update_status_bar(self, node_id: int):
        if not self.ctx.is_project_open():
            return
        children = self.ctx.database_service.get_children(node_id)
        files = self.ctx.database_service.get_files_by_node(node_id)
        self.status_bar.showMessage(f"子节点: {len(children)} | 文件: {len(files)}")
