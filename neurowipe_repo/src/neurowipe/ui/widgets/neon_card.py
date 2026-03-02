"""NeonCard — Card container with glow border effect."""

from __future__ import annotations

from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QFrame, QVBoxLayout, QGraphicsDropShadowEffect

from ...theme.colors import Colors


class NeonCard(QFrame):
    """A card container with neon border glow."""

    def __init__(self, title: str = "", color: str = Colors.CYAN, parent=None):
        super().__init__(parent)
        self._title = title
        self._color = color
        self._glow_radius = 0.0

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(8)

        # Glow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(color))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

        self._anim = QPropertyAnimation(self, b"glow_radius")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            NeonCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
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
        self._anim.setEndValue(15.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_radius)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)

    @property
    def card_layout(self) -> QVBoxLayout:
        return self._layout

    def set_color(self, color: str) -> None:
        self._color = color
        self._shadow.setColor(QColor(color))
        self._apply_style()
