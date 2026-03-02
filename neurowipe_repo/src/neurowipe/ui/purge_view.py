"""PurgeView — Main deletion interface with filters, channel tree, and progress."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..core.models import DeletionJob, SearchFilter
from ..theme.colors import Colors
from ..utils.formatters import format_count, format_duration, format_rate
from .log_view import LogView
from .widgets.channel_tree import ChannelTree
from .widgets.glow_label import GlowLabel
from .widgets.neon_button import NeonButton
from .widgets.neon_checkbox import NeonCheckBox
from .widgets.neon_line_edit import NeonLineEdit
from .widgets.neon_progress_bar import NeonProgressBar


class PurgeView(QWidget):
    """Primary screen: filters, channel tree, progress, and log."""

    scan_requested = Signal(object)  # SearchFilter
    purge_requested = Signal(object)  # SearchFilter
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = GlowLabel("MESSAGE PURGE", Colors.CYAN, font_size=18, glow_radius=10)
        main_layout.addWidget(title)

        # Main splitter: top (filters + tree) / bottom (log + progress)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(3)

        # === Top section ===
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        # --- Left: Filters ---
        filter_panel = QFrame()
        filter_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        filter_layout = QVBoxLayout(filter_panel)
        filter_layout.setContentsMargins(12, 12, 12, 12)
        filter_layout.setSpacing(10)

        filter_title = QLabel("FILTERS")
        filter_title.setStyleSheet(
            f"color: {Colors.CYAN}; font-size: 11px; letter-spacing: 2px; font-weight: bold;"
        )
        filter_layout.addWidget(filter_title)

        # Date range
        date_label = QLabel("Date Range")
        date_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        filter_layout.addWidget(date_label)

        date_row = QHBoxLayout()
        self._after_date = QDateEdit()
        self._after_date.setCalendarPopup(True)
        self._after_date.setDate(datetime(2015, 1, 1).date())
        self._after_date.setDisplayFormat("yyyy-MM-dd")
        date_row.addWidget(QLabel("From:"))
        date_row.addWidget(self._after_date)

        self._before_date = QDateEdit()
        self._before_date.setCalendarPopup(True)
        self._before_date.setDate(datetime.now().date())
        self._before_date.setDisplayFormat("yyyy-MM-dd")
        date_row.addWidget(QLabel("To:"))
        date_row.addWidget(self._before_date)
        filter_layout.addLayout(date_row)

        # Keyword / regex
        keyword_label = QLabel("Content Filter")
        keyword_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        filter_layout.addWidget(keyword_label)

        self._content_edit = NeonLineEdit("Keyword or phrase...")
        filter_layout.addWidget(self._content_edit)

        # Has filters
        has_label = QLabel("Contains")
        has_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        filter_layout.addWidget(has_label)

        self._has_link = NeonCheckBox("Links")
        self._has_file = NeonCheckBox("Files")
        self._has_embed = NeonCheckBox("Embeds")

        has_row = QHBoxLayout()
        has_row.addWidget(self._has_link)
        has_row.addWidget(self._has_file)
        has_row.addWidget(self._has_embed)
        filter_layout.addLayout(has_row)

        filter_layout.addStretch()

        # Scan / Purge buttons
        self._scan_btn = NeonButton("SCAN", Colors.ELECTRIC_PURPLE)
        self._scan_btn.clicked.connect(self._on_scan)
        filter_layout.addWidget(self._scan_btn)

        self._purge_btn = NeonButton("PURGE", Colors.ERROR)
        self._purge_btn.clicked.connect(self._on_purge)
        filter_layout.addWidget(self._purge_btn)

        top_layout.addWidget(filter_panel, 1)

        # --- Right: Channel tree ---
        tree_panel = QFrame()
        tree_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        tree_layout = QVBoxLayout(tree_panel)
        tree_layout.setContentsMargins(12, 12, 12, 12)
        tree_layout.setSpacing(8)

        tree_header = QHBoxLayout()
        tree_title = QLabel("TARGETS")
        tree_title.setStyleSheet(
            f"color: {Colors.CYAN}; font-size: 11px; letter-spacing: 2px; font-weight: bold;"
        )
        tree_header.addWidget(tree_title)
        tree_header.addStretch()

        select_all_btn = NeonButton("All", Colors.TEXT_SECONDARY)
        select_all_btn.setFixedHeight(24)
        select_all_btn.setFixedWidth(50)
        select_all_btn.clicked.connect(lambda: self._channel_tree.select_all())
        tree_header.addWidget(select_all_btn)

        deselect_btn = NeonButton("None", Colors.TEXT_SECONDARY)
        deselect_btn.setFixedHeight(24)
        deselect_btn.setFixedWidth(50)
        deselect_btn.clicked.connect(lambda: self._channel_tree.deselect_all())
        tree_header.addWidget(deselect_btn)

        tree_layout.addLayout(tree_header)

        self._channel_tree = ChannelTree()
        tree_layout.addWidget(self._channel_tree)

        top_layout.addWidget(tree_panel, 1)

        splitter.addWidget(top_widget)

        # === Bottom section ===
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)

        # Log panel (left)
        self._log_view = LogView()
        bottom_layout.addWidget(self._log_view, 1)

        # Progress panel (right)
        progress_panel = QFrame()
        progress_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_panel)
        progress_layout.setContentsMargins(12, 12, 12, 12)
        progress_layout.setSpacing(8)

        # Stats
        self._stats_label = QLabel("Ready")
        self._stats_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        self._stats_label.setWordWrap(True)
        progress_layout.addWidget(self._stats_label)

        # Progress bar
        self._progress_bar = NeonProgressBar()
        progress_layout.addWidget(self._progress_bar)

        # Scan result
        self._scan_result = QLabel("")
        self._scan_result.setStyleSheet(f"color: {Colors.CYAN}; font-size: 13px;")
        self._scan_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self._scan_result)

        progress_layout.addStretch()

        # Control buttons
        control_row = QHBoxLayout()
        self._pause_btn = NeonButton("PAUSE", Colors.WARNING)
        self._pause_btn.clicked.connect(self._on_pause)
        self._pause_btn.setEnabled(False)
        control_row.addWidget(self._pause_btn)

        self._cancel_btn = NeonButton("CANCEL", Colors.ERROR)
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        self._cancel_btn.setEnabled(False)
        control_row.addWidget(self._cancel_btn)

        progress_layout.addLayout(control_row)

        bottom_layout.addWidget(progress_panel, 1)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 200])

        main_layout.addWidget(splitter)

    @property
    def channel_tree(self) -> ChannelTree:
        return self._channel_tree

    @property
    def log_view(self) -> LogView:
        return self._log_view

    def _build_filter(self) -> SearchFilter:
        """Build a SearchFilter from current UI state."""
        guild_ids, channel_ids = self._channel_tree.get_selected()

        after_date = self._after_date.date().toPython()
        before_date = self._before_date.date().toPython()

        content = self._content_edit.text().strip() or None

        return SearchFilter(
            guild_ids=guild_ids,
            channel_ids=channel_ids,
            after=datetime.combine(after_date, datetime.min.time()) if after_date else None,
            before=datetime.combine(before_date, datetime.max.time()) if before_date else None,
            content=content,
            has_link=self._has_link.isChecked() or None,
            has_file=self._has_file.isChecked() or None,
            has_embed=self._has_embed.isChecked() or None,
        )

    def _on_scan(self) -> None:
        self.scan_requested.emit(self._build_filter())

    def _on_purge(self) -> None:
        self.purge_requested.emit(self._build_filter())

    def _on_pause(self) -> None:
        if self._pause_btn.text() == "PAUSE":
            self.pause_requested.emit()
            self._pause_btn.setText("RESUME")
            self._pause_btn.set_color(Colors.SUCCESS)
        else:
            self.resume_requested.emit()
            self._pause_btn.setText("PAUSE")
            self._pause_btn.set_color(Colors.WARNING)

    def set_scan_result(self, count: int) -> None:
        self._scan_result.setText(f"Found {format_count(count)} messages")

    def set_running(self, running: bool) -> None:
        """Toggle UI state for active deletion."""
        self._scan_btn.setEnabled(not running)
        self._purge_btn.setEnabled(not running)
        self._pause_btn.setEnabled(running)
        self._cancel_btn.setEnabled(running)
        if not running:
            self._pause_btn.setText("PAUSE")
            self._pause_btn.set_color(Colors.WARNING)

    def update_progress(self, job: DeletionJob) -> None:
        """Update progress display from a DeletionJob."""
        self._progress_bar.set_max(max(1, job.total_messages))
        self._progress_bar.set_value(
            job.deleted_count + job.failed_count + job.skipped_count
        )

        stats_parts = [
            f"Deleted: {format_count(job.deleted_count)}",
            f"Failed: {job.failed_count}",
            f"Total: {format_count(job.total_messages)}",
        ]
        if job.rate > 0:
            stats_parts.append(f"Rate: {format_rate(job.rate)}")
        if job.started_at:
            elapsed = (datetime.now() - job.started_at).total_seconds()
            stats_parts.append(f"Time: {format_duration(elapsed)}")

        self._stats_label.setText(" | ".join(stats_parts))

    def reset_progress(self) -> None:
        self._progress_bar.set_value(0)
        self._stats_label.setText("Ready")
        self._scan_result.setText("")
