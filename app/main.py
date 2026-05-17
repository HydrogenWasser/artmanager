"""Application entry point."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.app_context import AppContext
from ui.main_window import MainWindow
from ui.style import apply_dark_theme


def main():
    # Enable high DPI scaling (must be before QApplication creation)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("美术资源管理工具")
    app.setApplicationVersion("0.1.0")

    apply_dark_theme(app)

    ctx = AppContext()
    window = MainWindow(ctx)
    window.show()

    sys.exit(app.exec())
