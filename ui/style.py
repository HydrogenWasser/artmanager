"""UI styles and themes for Pixel Asset Manager."""

DARK_STYLE = """
QMainWindow {
    background-color: #1E1E1E;
    color: #E6E6E6;
}

QWidget {
    background-color: #1E1E1E;
    color: #E6E6E6;
    font-size: 13px;
}

QSplitter::handle {
    background-color: #3F3F46;
}

QTreeWidget {
    background-color: #252526;
    border: none;
    color: #E6E6E6;
    outline: none;
}

QTreeWidget::item {
    padding: 4px 0px;
}

QTreeWidget::item:selected {
    background-color: #3A3A3D;
}

QTreeWidget::item:hover {
    background-color: #2A2A2D;
}

QTreeWidget::item:selected:hover {
    background-color: #3A3A3D;
}

QHeaderView::section {
    background-color: #252526;
    color: #A0A0A0;
    padding: 5px;
    border: none;
    border-bottom: 1px solid #3F3F46;
}

QScrollArea {
    border: none;
}

QScrollBar:vertical {
    background-color: #1E1E1E;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #3F3F46;
    min-height: 30px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1E1E1E;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #3F3F46;
    min-width: 30px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QFrame#AssetCard {
    background-color: #2D2D30;
    border: 1px solid #3F3F46;
    border-radius: 8px;
}

QFrame#AssetCard:hover {
    background-color: #3A3A3D;
    border: 1px solid #6CA0DC;
}

QPushButton {
    background-color: #333333;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
    padding: 6px 12px;
    color: #E6E6E6;
}

QPushButton:hover {
    background-color: #444444;
    border: 1px solid #6CA0DC;
}

QPushButton:pressed {
    background-color: #555555;
}

QPushButton:disabled {
    background-color: #2A2A2A;
    color: #666666;
    border: 1px solid #333333;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: #2D2D30;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    padding: 5px;
    color: #E6E6E6;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #6CA0DC;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2D2D30;
    border: 1px solid #3F3F46;
    color: #E6E6E6;
    selection-background-color: #3A3A3D;
}

QMenu {
    background-color: #2D2D30;
    border: 1px solid #3F3F46;
    color: #E6E6E6;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #3A3A3D;
}

QMenu::separator {
    height: 1px;
    background-color: #3F3F46;
    margin: 4px 8px;
}

QToolBar {
    background-color: #252526;
    border-bottom: 1px solid #3F3F46;
    spacing: 4px;
    padding: 4px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: #E6E6E6;
}

QToolButton:hover {
    background-color: #3A3A3D;
    border: 1px solid #4A4A4A;
}

QStatusBar {
    background-color: #252526;
    color: #A0A0A0;
    border-top: 1px solid #3F3F46;
}

QLabel {
    color: #E6E6E6;
}

QLabel#secondary {
    color: #A0A0A0;
}

QDialog {
    background-color: #1E1E1E;
}

QGroupBox {
    border: 1px solid #3F3F46;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #A0A0A0;
}
"""


def apply_dark_theme(app):
    """Apply dark theme to the QApplication."""
    app.setStyleSheet(DARK_STYLE)
