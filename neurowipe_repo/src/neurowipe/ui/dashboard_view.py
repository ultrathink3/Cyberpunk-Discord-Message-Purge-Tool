"""DashboardView — Analytics charts and stat cards."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..core.models import AnalyticsData, SearchFilter
from ..theme.colors import Colors
from ..utils.formatters import format_count
from .charts.activity_heatmap import ActivityHeatmap
from .charts.message_timeline import MessageTimeline
from .charts.server_pie_chart import ServerPieChart
from .charts.storage_bar_chart import StorageBarChart
from .widgets.glow_label import GlowLabel
from .widgets.neon_button import NeonButton
from .widgets.neon_card import NeonCard
from .widgets.neon_combo_box import NeonComboBox


class StatCard(NeonCard):
    """Small stat display card."""

    def __init__(self, title: str, value: str, color: str = Colors.CYAN, parent=None):
        super().__init__(color=color, parent=parent)
        self.setFixedHeight(90)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 10px; "
            f"letter-spacing: 2px; background: transparent;"
        )
        self.card_layout.addWidget(title_label)

        self._value_label = GlowLabel(value, color, font_size=22, glow_radius=8)
        self.card_layout.addWidget(self._value_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)


class DashboardView(QWidget):
    """Analytics dashboard with charts and stat cards."""

    compute_requested = Signal(object)  # SearchFilter

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = GlowLabel("ANALYTICS", Colors.ELECTRIC_PURPLE, font_size=18, glow_radius=10)
        header.addWidget(title)
        header.addStretch()

        self._period_combo = NeonComboBox()
        self._period_combo.addItems(["All Time", "Last 30 Days", "Last 7 Days", "Last 24 Hours"])
        header.addWidget(self._period_combo)

        self._refresh_btn = NeonButton("REFRESH", Colors.ELECTRIC_PURPLE)
        self._refresh_btn.clicked.connect(self._on_refresh)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)

        # Stat cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._total_card = StatCard("TOTAL MESSAGES", "0", Colors.CYAN)
        cards_row.addWidget(self._total_card)

        self._servers_card = StatCard("SERVERS", "0", Colors.MAGENTA)
        cards_row.addWidget(self._servers_card)

        self._storage_card = StatCard("EST. STORAGE", "0 MB", Colors.ELECTRIC_PURPLE)
        cards_row.addWidget(self._storage_card)

        layout.addLayout(cards_row)

        # Charts area
        charts_top = QHBoxLayout()
        charts_top.setSpacing(12)

        # Timeline
        timeline_container = QWidget()
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_label = QLabel("MESSAGE ACTIVITY")
        timeline_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 10px; letter-spacing: 2px;"
        )
        timeline_layout.addWidget(timeline_label)
        self._timeline = MessageTimeline()
        timeline_layout.addWidget(self._timeline)
        charts_top.addWidget(timeline_container, 2)

        # Pie chart
        pie_container = QWidget()
        pie_layout = QVBoxLayout(pie_container)
        pie_layout.setContentsMargins(0, 0, 0, 0)
        pie_label = QLabel("MESSAGES PER SERVER")
        pie_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 10px; letter-spacing: 2px;"
        )
        pie_layout.addWidget(pie_label)
        self._pie_chart = ServerPieChart()
        pie_layout.addWidget(self._pie_chart)
        charts_top.addWidget(pie_container, 1)

        layout.addLayout(charts_top)

        # Bottom charts
        charts_bottom = QHBoxLayout()
        charts_bottom.setSpacing(12)

        # Heatmap
        heatmap_container = QWidget()
        heatmap_layout = QVBoxLayout(heatmap_container)
        heatmap_layout.setContentsMargins(0, 0, 0, 0)
        heatmap_label = QLabel("ACTIVITY HEATMAP")
        heatmap_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 10px; letter-spacing: 2px;"
        )
        heatmap_layout.addWidget(heatmap_label)
        self._heatmap = ActivityHeatmap()
        heatmap_layout.addWidget(self._heatmap)
        charts_bottom.addWidget(heatmap_container, 1)

        # Bar chart
        bar_container = QWidget()
        bar_layout = QVBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_label = QLabel("TOP CHANNELS")
        bar_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 10px; letter-spacing: 2px;"
        )
        bar_layout.addWidget(bar_label)
        self._bar_chart = StorageBarChart()
        bar_layout.addWidget(self._bar_chart)
        charts_bottom.addWidget(bar_container, 1)

        layout.addLayout(charts_bottom)

    def update_data(self, data: AnalyticsData) -> None:
        """Populate all charts and cards with analytics data."""
        self._total_card.set_value(format_count(data.total_messages))
        self._servers_card.set_value(str(data.total_servers))
        self._storage_card.set_value(f"{data.estimated_storage_mb:.1f} MB")

        # Timeline
        if data.messages_by_date:
            sorted_dates = sorted(data.messages_by_date.keys())
            counts = [data.messages_by_date[d] for d in sorted_dates]
            self._timeline.set_data(sorted_dates, counts)

        # Pie chart
        if data.messages_by_server:
            self._pie_chart.set_data(data.messages_by_server)

        # Heatmap
        if data.activity_heatmap:
            self._heatmap.set_data(data.activity_heatmap)

        # Bar chart
        if data.messages_by_channel:
            self._bar_chart.set_data(data.messages_by_channel)

    def _on_refresh(self) -> None:
        self.compute_requested.emit(SearchFilter())

    def clear_data(self) -> None:
        self._total_card.set_value("0")
        self._servers_card.set_value("0")
        self._storage_card.set_value("0 MB")
        self._timeline.clear_data()
        self._pie_chart.clear_data()
        self._heatmap.clear_data()
        self._bar_chart.clear_data()
