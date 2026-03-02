"""AboutDialog — About NEUROWIPE information dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from ...constants import APP_NAME, APP_TAGLINE, APP_VERSION
from ...theme.colors import Colors
from ..widgets.animated_logo import AnimatedLogo
from ..widgets.neon_button import NeonButton


class AboutDialog(QDialog):
    """Dialog displaying application info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About NEUROWIPE")
        self.setFixedSize(380, 320)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.CYAN};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        self._logo = AnimatedLogo()
        layout.addWidget(self._logo)

        # Version
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(version_label)

        # Description
        desc_label = QLabel(
            "Cyberpunk Discord Message Purge Tool\n"
            "Bulk-delete your own Discord messages\n"
            "with analytics, export, and scheduling."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Close button
        close_btn = NeonButton("CLOSE", Colors.CYAN)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._logo.start_animation()

    def closeEvent(self, event):
        self._logo.stop_animation()
        super().closeEvent(event)
