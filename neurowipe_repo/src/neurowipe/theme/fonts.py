"""Font loading and management for cyberpunk theme."""

from __future__ import annotations

import logging

from PySide6.QtGui import QFont, QFontDatabase

from ..utils.platform_utils import resource_path

logger = logging.getLogger("neurowipe.fonts")

# Font family names
FONT_MONO = "Share Tech Mono"
FONT_DISPLAY = "Orbitron"
FONT_FALLBACK_MONO = "Consolas"
FONT_FALLBACK_DISPLAY = "Arial"

_fonts_loaded = False


def load_fonts() -> None:
    """Load bundled fonts into Qt's font database."""
    global _fonts_loaded
    if _fonts_loaded:
        return

    font_files = [
        "fonts/ShareTechMono-Regular.ttf",
        "fonts/Orbitron-Regular.ttf",
        "fonts/Orbitron-Bold.ttf",
        "fonts/Orbitron-Medium.ttf",
    ]

    for font_file in font_files:
        path = resource_path(font_file)
        if path.exists():
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(font_id)
                logger.debug(f"Loaded font: {families}")
            else:
                logger.warning(f"Failed to load font: {path}")
        else:
            logger.debug(f"Font file not found: {path}")

    _fonts_loaded = True


def get_mono_font(size: int = 11) -> QFont:
    """Get the monospace UI font."""
    families = QFontDatabase.families()
    family = FONT_MONO if FONT_MONO in families else FONT_FALLBACK_MONO
    font = QFont(family, size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def get_display_font(size: int = 14, bold: bool = False) -> QFont:
    """Get the display/header font."""
    families = QFontDatabase.families()
    family = FONT_DISPLAY if FONT_DISPLAY in families else FONT_FALLBACK_DISPLAY
    font = QFont(family, size)
    if bold:
        font.setBold(True)
    return font


def get_logo_font(size: int = 28) -> QFont:
    """Get the font for the NEUROWIPE logo."""
    return get_display_font(size, bold=True)
