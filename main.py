#!/usr/bin/env python3
"""SecureIPTV - entry point and application stylesheet."""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from player.main_window import MainWindow

_STYLESHEET = """
    QMainWindow, QWidget  { background-color:#1e1e2e; color:#cdd6f4; }
    QPushButton {
        background-color:#313244; color:#cdd6f4;
        border:1px solid #45475a; border-radius:4px;
        padding:4px 10px; font-size:13px;
    }
    QPushButton:hover   { background-color:#45475a; }
    QPushButton:checked { background-color:#89b4fa; color:#1e1e2e; }
    QLineEdit, QComboBox {
        background-color:#313244; color:#cdd6f4;
        border:1px solid #45475a; border-radius:4px; padding:4px 8px;
    }
    QListView, QListWidget {
        background-color:#181825; color:#cdd6f4;
        border:1px solid #45475a; outline:none;
    }
    QListView::item:selected { background-color:#89b4fa; color:#1e1e2e; }
    QListView::item:hover    { background-color:#313244; }
    QSlider::groove:horizontal { background:#313244; height:4px; border-radius:2px; }
    QSlider::handle:horizontal {
        background:#89b4fa; width:12px; height:12px;
        margin:-4px 0; border-radius:6px;
    }
    QSlider::sub-page:horizontal { background:#89b4fa; border-radius:2px; }
    QStatusBar     { background-color:#181825; color:#6c7086; font-size:11px; }
    QSplitter::handle { background-color:#45475a; width:2px; }
    QLabel         { color:#cdd6f4; }
    QTabWidget::pane { border:1px solid #45475a; }
    QTabBar::tab {
        background:#313244; color:#cdd6f4;
        padding:6px 14px; border-radius:4px 4px 0 0; margin-right:2px;
    }
    QTabBar::tab:selected { background:#89b4fa; color:#1e1e2e; }
    QTabBar::tab:hover    { background:#45475a; }
    QCheckBox { color:#cdd6f4; spacing:6px; }
    QCheckBox::indicator {
        width:14px; height:14px;
        background:#313244; border:1px solid #45475a; border-radius:3px;
    }
    QCheckBox::indicator:checked { background:#89b4fa; }
    QDialog, QMessageBox { background-color:#1e1e2e; color:#cdd6f4; }
    QScrollBar:vertical { background:#181825; width:8px; border-radius:4px; }
    QScrollBar::handle:vertical {
        background:#45475a; border-radius:4px; min-height:20px;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical { height:0; }
"""


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    for name in ("vlc", "urllib3"):
        logging.getLogger(name).setLevel(logging.ERROR)


def main() -> None:
    _configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("SecureIPTV")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SecureIPTV")
    app.setStyleSheet(_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
