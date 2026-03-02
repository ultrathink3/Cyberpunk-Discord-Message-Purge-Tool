"""Cyberpunk theme engine — loads QSS, sets palette, manages theme state."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .colors import Colors
from .fonts import load_fonts

logger = logging.getLogger("neurowipe.theme")

_QSS_PATH = Path(__file__).parent / "styles.qss"


class CyberpunkTheme:
    """Applies and manages the cyberpunk neon theme."""

    def __init__(self, app: QApplication):
        self._app = app
        self._accent_color = Colors.CYAN
        self._scanline_enabled = True
        self._animation_speed = 1.0

    def apply(self) -> None:
        """Apply the full cyberpunk theme."""
        load_fonts()
        self._set_palette()
        self._load_stylesheet()
        logger.info("Cyberpunk theme applied")

    def _set_palette(self) -> None:
        """Set the application QPalette for unthemed widgets."""
        palette = QPalette()

        palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_MAIN))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_INPUT))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_CARD))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.BG_HOVER))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BUTTON_BG))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(Colors.TEXT_BRIGHT))
        palette.setColor(QPalette.ColorRole.Link, QColor(self._accent_color))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self._accent_color))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT_BRIGHT))

        # Disabled colors
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(Colors.TEXT_MUTED),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(Colors.TEXT_MUTED),
        )

        self._app.setPalette(palette)

    def _load_stylesheet(self) -> None:
        """Load and apply the master QSS stylesheet."""
        if _QSS_PATH.exists():
            qss = _QSS_PATH.read_text(encoding="utf-8")
            # Replace accent color placeholder
            qss = qss.replace("#00f0ff", self._accent_color)
            self._app.setStyleSheet(qss)
        else:
            logger.warning(f"QSS file not found: {_QSS_PATH}")

    @property
    def accent_color(self) -> str:
        return self._accent_color

    @accent_color.setter
    def accent_color(self, color: str) -> None:
        self._accent_color = color
        self._load_stylesheet()
        self._set_palette()

    @property
    def scanline_enabled(self) -> bool:
        return self._scanline_enabled

    @scanline_enabled.setter
    def scanline_enabled(self, enabled: bool) -> None:
        self._scanline_enabled = enabled

    @property
    def animation_speed(self) -> float:
        return self._animation_speed

    @animation_speed.setter
    def animation_speed(self, speed: float) -> None:
        self._animation_speed = max(0.1, min(3.0, speed))
