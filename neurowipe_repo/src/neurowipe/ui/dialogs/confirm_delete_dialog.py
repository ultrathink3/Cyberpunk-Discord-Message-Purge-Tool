"""ConfirmDeleteDialog — Confirmation dialog before bulk deletion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from ...theme.colors import Colors
from ..widgets.glow_label import GlowLabel
from ..widgets.neon_button import NeonButton


class ConfirmDeleteDialog(QDialog):
    """Modal dialog to confirm bulk message deletion."""

    def __init__(self, message_count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Deletion")
        self.setFixedSize(420, 260)
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
        layout.setSpacing(16)

        # Warning icon
        warning_label = GlowLabel(
            "\u26a0", color=Colors.WARNING, font_size=32, glow_radius=20
        )
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)

        # Title
        title = GlowLabel(
            "CONFIRM PURGE", color=Colors.ERROR, font_size=16, glow_radius=10
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Message
        msg_label = QLabel(
            f"You are about to permanently delete\n"
            f"<b>{message_count:,}</b> messages.\n\n"
            f"This action cannot be undone."
        )
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        msg_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(msg_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = NeonButton("CANCEL", Colors.TEXT_SECONDARY)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._confirm_btn = NeonButton("PURGE", Colors.ERROR)
        self._confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._confirm_btn)

        layout.addLayout(btn_layout)
