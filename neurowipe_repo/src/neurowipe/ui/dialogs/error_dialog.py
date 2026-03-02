"""ErrorDialog — Styled error display dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QTextEdit

from ...theme.colors import Colors
from ..widgets.glow_label import GlowLabel
from ..widgets.neon_button import NeonButton


class ErrorDialog(QDialog):
    """Dialog for displaying error messages."""

    def __init__(self, title: str, message: str, details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error")
        self.setMinimumSize(420, 220)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.ERROR};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Error icon + title
        error_title = GlowLabel(
            f"\u2716 {title}", color=Colors.ERROR, font_size=14, glow_radius=10
        )
        layout.addWidget(error_title)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(msg_label)

        # Details (expandable)
        if details:
            details_edit = QTextEdit()
            details_edit.setReadOnly(True)
            details_edit.setPlainText(details)
            details_edit.setMaximumHeight(100)
            details_edit.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {Colors.BG_INPUT};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 6px;
                    color: {Colors.TEXT_MUTED};
                    font-size: 11px;
                    font-family: "Share Tech Mono", monospace;
                }}
            """)
            layout.addWidget(details_edit)

        layout.addStretch()

        # Close button
        close_btn = NeonButton("CLOSE", Colors.ERROR)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    @classmethod
    def show_error(
        cls, title: str, message: str, details: str = "", parent=None
    ) -> None:
        """Convenience method to show an error dialog."""
        dialog = cls(title, message, details, parent)
        dialog.exec()
