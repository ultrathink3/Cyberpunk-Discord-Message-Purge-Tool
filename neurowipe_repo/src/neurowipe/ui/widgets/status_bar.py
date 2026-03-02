"""StatusBar — Custom status bar with neon styling."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ...theme.colors import Colors


class StatusBar(QWidget):
    """Custom status bar with cyberpunk neon indicators."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            StatusBar {{
                background-color: {Colors.SIDEBAR_BG};
                border-top: 1px solid {Colors.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)

        # Connection status indicator
        self._connection_dot = QLabel("\u25cf")
        self._connection_dot.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(self._connection_dot)

        self._connection_label = QLabel("Disconnected")
        self._connection_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self._connection_label)

        layout.addStretch()

        # Rate info
        self._rate_label = QLabel("")
        self._rate_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._rate_label)

        # Version
        self._version_label = QLabel("NEUROWIPE v1.0.0")
        self._version_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._version_label)

    def set_connected(self, username: str) -> None:
        self._connection_dot.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 10px;")
        self._connection_label.setText(f"Connected: {username}")
        self._connection_label.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 11px;")

    def set_disconnected(self) -> None:
        self._connection_dot.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        self._connection_label.setText("Disconnected")
        self._connection_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")

    def set_rate_info(self, text: str) -> None:
        self._rate_label.setText(text)

    def set_error(self, message: str) -> None:
        self._connection_dot.setStyleSheet(f"color: {Colors.ERROR}; font-size: 10px;")
        self._connection_label.setText(message)
        self._connection_label.setStyleSheet(f"color: {Colors.ERROR}; font-size: 11px;")
