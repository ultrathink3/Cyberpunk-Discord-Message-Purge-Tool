"""MessageTimeline — Line chart showing message activity over time."""

from __future__ import annotations

from datetime import datetime

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ...theme.colors import Colors
from .chart_theme import get_neon_brush, get_neon_pen, style_plot_widget


class MessageTimeline(QWidget):
    """Line chart displaying message count over time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        style_plot_widget(self._plot_widget)
        self._plot_widget.setLabel("left", "Messages")
        self._plot_widget.setLabel("bottom", "Date")
        layout.addWidget(self._plot_widget)

        self._curve = None
        self._fill = None

    def set_data(self, dates: list[str], counts: list[int]) -> None:
        """Set timeline data. dates are 'YYYY-MM-DD' strings."""
        self._plot_widget.clear()

        if not dates or not counts:
            return

        # Convert dates to numeric x values
        x_vals = list(range(len(dates)))
        y_vals = counts

        # Filled area
        self._fill = pg.PlotCurveItem(
            x=x_vals,
            y=y_vals,
            pen=get_neon_pen(Colors.CYAN, 2),
            fillLevel=0,
            brush=get_neon_brush(Colors.CYAN, 40),
        )
        self._plot_widget.addItem(self._fill)

        # Set x-axis labels
        if len(dates) > 10:
            # Show every Nth label
            step = max(1, len(dates) // 10)
            ticks = [(i, dates[i]) for i in range(0, len(dates), step)]
        else:
            ticks = [(i, d) for i, d in enumerate(dates)]

        axis = self._plot_widget.getPlotItem().getAxis("bottom")
        axis.setTicks([ticks])

    def clear_data(self) -> None:
        self._plot_widget.clear()
