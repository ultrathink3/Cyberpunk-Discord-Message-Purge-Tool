"""NeonLineEdit — Line edit with glow focus effect."""

from __future__ import annotations

from PySide6.QtCore import Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLineEdit

from ...theme.colors import Colors


class NeonLineEdit(QLineEdit):
    """Line edit with neon glow on focus."""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._glow_radius = 0.0

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(Colors.CYAN))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

        self._anim = QPropertyAnimation(self, b"glow_radius")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    @Property(float)
    def glow_radius(self) -> float:
        return self._glow_radius

    @glow_radius.setter
    def glow_radius(self, value: float) -> None:
        self._glow_radius = value
        self._shadow.setBlurRadius(value)

    def focusInEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_radius)
        self._anim.setEndValue(12.0)
        self._anim.start()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_radius)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().focusOutEvent(event)
