"""NeonButton — Animated glow button with cyberpunk styling."""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QPushButton

from ...theme.colors import Colors


class NeonButton(QPushButton):
    """A push button with animated neon glow on hover/click."""

    def __init__(
        self,
        text: str = "",
        color: str = Colors.CYAN,
        parent=None,
    ):
        super().__init__(text, parent)
        self._glow_color = color
        self._glow_radius = 0.0

        # Glow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(color))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

        # Hover animation
        self._anim = QPropertyAnimation(self, b"glow_radius")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.setMinimumHeight(36)
        self.setCursor(self.cursor())
        self._apply_style()

    def _apply_style(self) -> None:
        r, g, b = Colors.to_rgb_tuple(self._glow_color)
        self.setStyleSheet(f"""
            NeonButton {{
                background-color: rgba({r}, {g}, {b}, 0.12);
                border: 1px solid {self._glow_color};
                border-radius: 6px;
                padding: 8px 20px;
                color: {self._glow_color};
                font-weight: bold;
                font-size: 13px;
            }}
            NeonButton:hover {{
                background-color: rgba({r}, {g}, {b}, 0.22);
            }}
            NeonButton:pressed {{
                background-color: rgba({r}, {g}, {b}, 0.35);
            }}
            NeonButton:disabled {{
                background-color: rgba({r}, {g}, {b}, 0.05);
                border-color: {Colors.BORDER};
                color: {Colors.TEXT_MUTED};
            }}
        """)

    @Property(float)
    def glow_radius(self) -> float:
        return self._glow_radius

    @glow_radius.setter
    def glow_radius(self, value: float) -> None:
        self._glow_radius = value
        self._shadow.setBlurRadius(value)

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_radius)
        self._anim.setEndValue(20.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_radius)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)

    def set_color(self, color: str) -> None:
        """Change the neon color."""
        self._glow_color = color
        self._shadow.setColor(QColor(color))
        self._apply_style()

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(max(hint.width(), 100), max(hint.height(), 36))
