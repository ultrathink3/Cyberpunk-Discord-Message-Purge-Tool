"""HeatmapWidget — GitHub-style activity grid with neon color intensity."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget

from ...theme.colors import Colors


class HeatmapWidget(QWidget):
    """Activity heatmap showing day-of-week vs hour grid."""

    DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    HOURS = [f"{h:02d}" for h in range(24)]
    CELL_SIZE = 18
    CELL_GAP = 2
    LABEL_WIDTH = 35
    LABEL_HEIGHT = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[tuple[int, int], int] = {}
        self._max_value = 1

        total_w = self.LABEL_WIDTH + (self.CELL_SIZE + self.CELL_GAP) * 24 + 10
        total_h = self.LABEL_HEIGHT + (self.CELL_SIZE + self.CELL_GAP) * 7 + 10
        self.setMinimumSize(total_w, total_h)

    def set_data(self, data: dict[tuple[int, int], int]) -> None:
        """Set heatmap data. Keys are (day_of_week, hour) tuples."""
        self._data = data
        self._max_value = max(data.values()) if data else 1
        self.update()

    def _get_color(self, value: int) -> QColor:
        """Map a value to a neon color intensity."""
        if value == 0:
            return QColor(Colors.BG_CARD)

        ratio = value / self._max_value if self._max_value > 0 else 0
        ratio = max(0.15, ratio)  # Minimum visibility

        # Interpolate from dark cyan to bright cyan
        r = int(0 + ratio * 0)
        g = int(30 + ratio * 210)
        b = int(40 + ratio * 215)
        return QColor(r, g, b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Share Tech Mono", 9)
        painter.setFont(font)

        # Draw hour labels (top)
        painter.setPen(QColor(Colors.TEXT_MUTED))
        for h in range(24):
            if h % 3 == 0:
                x = self.LABEL_WIDTH + h * (self.CELL_SIZE + self.CELL_GAP)
                painter.drawText(
                    QRectF(x, 0, self.CELL_SIZE, self.LABEL_HEIGHT),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{h}",
                )

        # Draw day labels (left) and cells
        for d in range(7):
            y = self.LABEL_HEIGHT + d * (self.CELL_SIZE + self.CELL_GAP)

            # Day label
            painter.setPen(QColor(Colors.TEXT_MUTED))
            painter.drawText(
                QRectF(0, y, self.LABEL_WIDTH - 4, self.CELL_SIZE),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                self.DAYS[d],
            )

            # Cells for each hour
            for h in range(24):
                x = self.LABEL_WIDTH + h * (self.CELL_SIZE + self.CELL_GAP)
                value = self._data.get((d, h), 0)
                color = self._get_color(value)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(
                    QRectF(x, y, self.CELL_SIZE, self.CELL_SIZE), 3, 3
                )

                # Border
                painter.setPen(QPen(QColor(Colors.BORDER), 0.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(
                    QRectF(x, y, self.CELL_SIZE, self.CELL_SIZE), 3, 3
                )

        painter.end()
