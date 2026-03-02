"""ScanlineOverlay — CRT scanline effect overlay."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ...theme.colors import Colors


class ScanlineOverlay(QWidget):
    """Transparent overlay that renders CRT scanlines over the entire window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._enabled = True
        self._opacity = 0.03
        self._line_spacing = 3
        self._scroll_offset = 0

        # Slow scroll animation
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._scroll)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if value:
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def start(self) -> None:
        if self._enabled:
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _scroll(self) -> None:
        self._scroll_offset = (self._scroll_offset + 1) % self._line_spacing
        self.update()

    def paintEvent(self, event):
        if not self._enabled:
            return

        painter = QPainter(self)
        pen = QPen(QColor(0, 0, 0, int(255 * self._opacity)))
        pen.setWidth(1)
        painter.setPen(pen)

        h = self.height()
        w = self.width()

        y = self._scroll_offset
        while y < h:
            painter.drawLine(0, y, w, y)
            y += self._line_spacing

        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
