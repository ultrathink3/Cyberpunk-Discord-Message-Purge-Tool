"""StorageBarChart — Bar chart showing storage usage per server."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ...theme.colors import Colors
from .chart_theme import CHART_COLORS, get_neon_brush, style_plot_widget


class StorageBarChart(QWidget):
    """Horizontal bar chart for per-server message counts or storage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        style_plot_widget(self._plot_widget)
        self._plot_widget.setLabel("bottom", "Messages")
        layout.addWidget(self._plot_widget)

    def set_data(self, data: dict[str, int]) -> None:
        """Set bar chart data as {label: count}."""
        self._plot_widget.clear()

        if not data:
            return

        # Sort and take top 10
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        labels = [name[:15] for name, _ in sorted_data]
        values = [count for _, count in sorted_data]

        x = list(range(len(values)))

        # Create bar items
        for i, (xi, val) in enumerate(zip(x, values)):
            color = QColor(CHART_COLORS[i % len(CHART_COLORS)])
            color.setAlpha(180)
            bar = pg.BarGraphItem(
                x=[xi],
                height=[val],
                width=0.6,
                brush=color,
                pen=pg.mkPen(color=Colors.BORDER, width=0.5),
            )
            self._plot_widget.addItem(bar)

        # Set tick labels
        ticks = [(i, label) for i, label in enumerate(labels)]
        axis = self._plot_widget.getPlotItem().getAxis("bottom")
        axis.setTicks([ticks])

    def clear_data(self) -> None:
        self._plot_widget.clear()
