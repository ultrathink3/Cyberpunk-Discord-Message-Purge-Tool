"""SchedulerView — Scheduled jobs table and management."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.models import ScheduledJob
from ..theme.colors import Colors
from ..utils.formatters import format_datetime
from .widgets.glow_label import GlowLabel
from .widgets.neon_button import NeonButton
from .widgets.neon_checkbox import NeonCheckBox


class SchedulerView(QWidget):
    """Scheduled jobs management view."""

    new_job_requested = Signal()
    edit_job_requested = Signal(int)  # job_id
    delete_job_requested = Signal(int)  # job_id
    toggle_job_requested = Signal(int, bool)  # job_id, enabled
    run_now_requested = Signal(int)  # job_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs: list[ScheduledJob] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = GlowLabel("SCHEDULER", Colors.WARNING, font_size=18, glow_radius=10)
        header.addWidget(title)
        header.addStretch()

        self._new_btn = NeonButton("NEW SCHEDULE", Colors.SUCCESS)
        self._new_btn.clicked.connect(self.new_job_requested.emit)
        header.addWidget(self._new_btn)

        layout.addLayout(header)

        # Description
        desc = QLabel(
            "Schedule automated message purges. "
            "Jobs continue running when minimized to system tray."
        )
        desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Enabled", "Name", "Schedule", "Target", "Last Run", "Next Run", "Actions"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._table)

    def set_jobs(self, jobs: list[ScheduledJob]) -> None:
        """Populate the table with scheduled jobs."""
        self._jobs = jobs
        self._table.setRowCount(0)

        for job in jobs:
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Enabled toggle
            toggle = NeonCheckBox("", Colors.SUCCESS)
            toggle.setChecked(job.enabled)
            toggle.toggled.connect(
                lambda checked, jid=job.id: self.toggle_job_requested.emit(jid, checked)
            )
            toggle_widget = QWidget()
            toggle_layout = QHBoxLayout(toggle_widget)
            toggle_layout.addWidget(toggle)
            toggle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            toggle_layout.setContentsMargins(4, 0, 4, 0)
            self._table.setCellWidget(row, 0, toggle_widget)

            # Name
            name_item = QTableWidgetItem(job.name)
            name_item.setForeground(QColor(Colors.TEXT_PRIMARY))
            self._table.setItem(row, 1, name_item)

            # Schedule (cron)
            cron_item = QTableWidgetItem(job.cron_expression)
            cron_item.setForeground(QColor(Colors.ELECTRIC_PURPLE))
            self._table.setItem(row, 2, cron_item)

            # Target
            targets = len(job.guild_ids) + len(job.channel_ids)
            target_item = QTableWidgetItem(f"{targets} targets")
            target_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self._table.setItem(row, 3, target_item)

            # Last run
            last_run = format_datetime(job.last_run) if job.last_run else "Never"
            last_item = QTableWidgetItem(last_run)
            last_item.setForeground(QColor(Colors.TEXT_MUTED))
            self._table.setItem(row, 4, last_item)

            # Next run
            next_run = format_datetime(job.next_run) if job.next_run else "—"
            next_item = QTableWidgetItem(next_run)
            next_item.setForeground(QColor(Colors.CYAN))
            self._table.setItem(row, 5, next_item)

            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            run_btn = NeonButton("\u25b6", Colors.SUCCESS)
            run_btn.setFixedSize(28, 28)
            run_btn.setToolTip("Run Now")
            run_btn.clicked.connect(
                lambda _, jid=job.id: self.run_now_requested.emit(jid)
            )
            actions_layout.addWidget(run_btn)

            edit_btn = NeonButton("\u270e", Colors.WARNING)
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Edit")
            edit_btn.clicked.connect(
                lambda _, jid=job.id: self.edit_job_requested.emit(jid)
            )
            actions_layout.addWidget(edit_btn)

            del_btn = NeonButton("\u2716", Colors.ERROR)
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip("Delete")
            del_btn.clicked.connect(
                lambda _, jid=job.id: self.delete_job_requested.emit(jid)
            )
            actions_layout.addWidget(del_btn)

            self._table.setCellWidget(row, 6, actions_widget)
