"""ActivityHeatmap — Wrapper around HeatmapWidget for charts panel."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..widgets.heatmap_widget import HeatmapWidget


class ActivityHeatmap(QWidget):
    """Activity heatmap chart wrapper for the dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._heatmap = HeatmapWidget()
        layout.addWidget(self._heatmap)

    def set_data(self, data: dict[tuple[int, int], int]) -> None:
        """Set heatmap data. Keys: (day_of_week, hour), values: count."""
        self._heatmap.set_data(data)

    def clear_data(self) -> None:
        self._heatmap.set_data({})
