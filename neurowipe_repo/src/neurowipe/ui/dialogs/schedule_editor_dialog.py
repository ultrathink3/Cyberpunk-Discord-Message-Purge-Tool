"""ScheduleEditorDialog — Create/edit scheduled deletion jobs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from ...core.models import ScheduledJob
from ...theme.colors import Colors
from ..widgets.glow_label import GlowLabel
from ..widgets.neon_button import NeonButton
from ..widgets.neon_checkbox import NeonCheckBox
from ..widgets.neon_line_edit import NeonLineEdit


class ScheduleEditorDialog(QDialog):
    """Dialog for creating or editing a scheduled deletion job."""

    def __init__(self, job: ScheduledJob | None = None, parent=None):
        super().__init__(parent)
        self._job = job
        self._is_edit = job is not None

        self.setWindowTitle("Edit Schedule" if self._is_edit else "New Schedule")
        self.setFixedSize(480, 400)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.ELECTRIC_PURPLE};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Title
        title_text = "EDIT SCHEDULE" if self._is_edit else "NEW SCHEDULE"
        title = GlowLabel(
            title_text, color=Colors.ELECTRIC_PURPLE, font_size=16, glow_radius=10
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Job name
        name_label = QLabel("Job Name")
        name_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(name_label)

        self._name_edit = NeonLineEdit("e.g., Weekly DM Cleanup")
        if self._is_edit and job:
            self._name_edit.setText(job.name)
        layout.addWidget(self._name_edit)

        # Cron expression
        cron_label = QLabel("Cron Expression")
        cron_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(cron_label)

        self._cron_edit = NeonLineEdit("e.g., 0 3 * * 0  (every Sunday at 3 AM)")
        if self._is_edit and job:
            self._cron_edit.setText(job.cron_expression)
        layout.addWidget(self._cron_edit)

        # Cron help
        help_label = QLabel("Format: minute hour day month day_of_week")
        help_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(help_label)

        # Options
        self._enabled_check = NeonCheckBox("Enabled", Colors.SUCCESS)
        self._enabled_check.setChecked(True if not self._is_edit else (job.enabled if job else True))
        layout.addWidget(self._enabled_check)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = NeonButton("CANCEL", Colors.TEXT_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = NeonButton(
            "SAVE" if self._is_edit else "CREATE",
            Colors.ELECTRIC_PURPLE,
        )
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    @property
    def job_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def cron_expression(self) -> str:
        return self._cron_edit.text().strip()

    @property
    def is_enabled(self) -> bool:
        return self._enabled_check.isChecked()
