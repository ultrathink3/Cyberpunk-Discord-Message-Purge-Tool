"""ServerPieChart — Pie chart showing messages per server using custom painting."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QBrush
from PySide6.QtWidgets import QWidget

from ...theme.colors import Colors
from .chart_theme import CHART_COLORS


class ServerPieChart(QWidget):
    """Custom-painted pie chart for messages per server."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[tuple[str, int]] = []  # (name, count)
        self._total = 0
        self.setMinimumSize(300, 250)

    def set_data(self, data: dict[str, int]) -> None:
        """Set pie chart data as {server_name: message_count}."""
        # Sort by count descending, take top 8
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_data) > 8:
            top = sorted_data[:7]
            other_count = sum(c for _, c in sorted_data[7:])
            top.append(("Other", other_count))
            sorted_data = top

        self._data = sorted_data
        self._total = sum(c for _, c in sorted_data)
        self.update()

    def paintEvent(self, event):
        if not self._data or self._total == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Pie area
        pie_size = min(w - 140, h - 20, 200)
        pie_rect = QRectF(10, (h - pie_size) / 2, pie_size, pie_size)

        start_angle = 90 * 16  # Start from top

        for i, (name, count) in enumerate(self._data):
            span = int((count / self._total) * 360 * 16)
            color = QColor(CHART_COLORS[i % len(CHART_COLORS)])

            painter.setPen(QPen(QColor(Colors.BG_CARD), 2))
            painter.setBrush(QBrush(color))
            painter.drawPie(pie_rect, start_angle, span)
            start_angle += span

        # Legend
        legend_x = pie_size + 30
        legend_y = max(10, (h - len(self._data) * 22) / 2)
        font = QFont("Share Tech Mono", 10)
        painter.setFont(font)

        for i, (name, count) in enumerate(self._data):
            y = legend_y + i * 22
            color = QColor(CHART_COLORS[i % len(CHART_COLORS)])

            # Color dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QRectF(legend_x, y + 2, 10, 10))

            # Label
            pct = (count / self._total * 100) if self._total > 0 else 0
            label = f"{name[:16]} ({pct:.0f}%)"
            painter.setPen(QColor(Colors.TEXT_SECONDARY))
            painter.drawText(QPointF(legend_x + 16, y + 12), label)

        painter.end()

    def clear_data(self) -> None:
        self._data = []
        self._total = 0
        self.update()
