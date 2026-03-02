"""GlowLabel — Text label with neon drop shadow glow."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel

from ...theme.colors import Colors


class GlowLabel(QLabel):
    """Label with neon glow drop shadow effect."""

    def __init__(
        self,
        text: str = "",
        color: str = Colors.CYAN,
        font_size: int = 14,
        glow_radius: float = 15.0,
        parent=None,
    ):
        super().__init__(text, parent)
        self._color = color

        # Set text color
        self.setStyleSheet(f"color: {color}; background: transparent;")

        # Glow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(glow_radius)
        shadow.setColor(QColor(color))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        if font_size:
            font = self.font()
            font.setPointSize(font_size)
            self.setFont(font)

    def set_color(self, color: str) -> None:
        self._color = color
        self.setStyleSheet(f"color: {color}; background: transparent;")
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setColor(QColor(color))

    def set_glow_radius(self, radius: float) -> None:
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            effect.setBlurRadius(radius)
