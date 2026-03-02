"""LogView — Real-time operation log panel."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..constants import LOG_MAX_LINES
from ..theme.colors import Colors


_LEVEL_COLORS = {
    "DEBUG": Colors.TEXT_MUTED,
    "INFO": Colors.CYAN,
    "WARNING": Colors.WARNING,
    "ERROR": Colors.ERROR,
    "CRITICAL": Colors.MAGENTA,
}


class LogView(QWidget):
    """Real-time scrolling operation log with color-coded levels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_scroll = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(24)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                padding: 2px 10px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                border-color: {Colors.CYAN};
                color: {Colors.CYAN};
            }}
        """)
        self._clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(self._clear_btn)

        self._autoscroll_btn = QPushButton("Auto-scroll: ON")
        self._autoscroll_btn.setFixedHeight(24)
        self._autoscroll_btn.setCheckable(True)
        self._autoscroll_btn.setChecked(True)
        self._autoscroll_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                padding: 2px 10px;
                font-size: 10px;
            }}
            QPushButton:checked {{
                border-color: {Colors.SUCCESS};
                color: {Colors.SUCCESS};
            }}
        """)
        self._autoscroll_btn.toggled.connect(self._toggle_autoscroll)
        toolbar.addWidget(self._autoscroll_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Log text area
        self._text_edit = QPlainTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setMaximumBlockCount(LOG_MAX_LINES)
        self._text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Colors.BG_DARKEST};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_SECONDARY};
                font-family: "Share Tech Mono", "Consolas", monospace;
                font-size: 11px;
                padding: 6px;
            }}
        """)
        layout.addWidget(self._text_edit)

    def append_log(self, level: str, message: str) -> None:
        """Add a log message with color coding."""
        color = _LEVEL_COLORS.get(level, Colors.TEXT_SECONDARY)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message + "\n", fmt)

        if self._auto_scroll:
            self._text_edit.ensureCursorVisible()

    def clear(self) -> None:
        self._text_edit.clear()

    def _toggle_autoscroll(self, checked: bool) -> None:
        self._auto_scroll = checked
        self._autoscroll_btn.setText(
            f"Auto-scroll: {'ON' if checked else 'OFF'}"
        )
