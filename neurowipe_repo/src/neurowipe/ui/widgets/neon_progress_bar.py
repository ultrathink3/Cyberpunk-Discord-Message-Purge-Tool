"""NeonProgressBar — Gradient progress bar with energy pulse animation."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ...theme.colors import Colors


class NeonProgressBar(QWidget):
    """Custom progress bar with cyan→purple→magenta gradient and pulse animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._max_value = 100.0
        self._pulse_offset = 0.0
        self._text = ""
        self.setMinimumHeight(26)
        self.setMaximumHeight(26)

        # Pulse animation
        self._pulse_anim = QPropertyAnimation(self, b"pulse_offset")
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

    @Property(float)
    def pulse_offset(self) -> float:
        return self._pulse_offset

    @pulse_offset.setter
    def pulse_offset(self, val: float) -> None:
        self._pulse_offset = val
        self.update()

    def set_value(self, value: float) -> None:
        self._value = min(value, self._max_value)
        self.update()

    def set_max(self, max_value: float) -> None:
        self._max_value = max(1, max_value)
        self.update()

    def set_text(self, text: str) -> None:
        self._text = text
        self.update()

    @property
    def progress(self) -> float:
        if self._max_value <= 0:
            return 0.0
        return self._value / self._max_value

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h // 2

        # Background track
        painter.setPen(QPen(QColor(Colors.BORDER), 1))
        painter.setBrush(QColor(Colors.BG_INPUT))
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Progress fill
        fill_width = int(w * self.progress)
        if fill_width > 0:
            gradient = QLinearGradient(0, 0, w, 0)
            offset = self._pulse_offset
            gradient.setColorAt(0, QColor(Colors.CYAN))
            gradient.setColorAt(0.5, QColor(Colors.ELECTRIC_PURPLE))
            gradient.setColorAt(1.0, QColor(Colors.MAGENTA))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(0, 0, fill_width, h, radius, radius)

            # Energy pulse highlight
            pulse_x = int(fill_width * offset)
            pulse_w = max(20, fill_width // 5)
            if pulse_x + pulse_w <= fill_width:
                highlight = QLinearGradient(pulse_x, 0, pulse_x + pulse_w, 0)
                highlight.setColorAt(0, QColor(255, 255, 255, 0))
                highlight.setColorAt(0.5, QColor(255, 255, 255, 60))
                highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.setBrush(highlight)
                painter.drawRoundedRect(
                    pulse_x, 0, pulse_w, h, radius, radius
                )

        # Text
        text = self._text or f"{self.progress * 100:.0f}%"
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
