"""ExportView — Export/backup interface."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ..core.models import ExportFormat
from ..theme.colors import Colors
from ..utils.platform_utils import get_default_export_dir
from .widgets.channel_tree import ChannelTree
from .widgets.glow_label import GlowLabel
from .widgets.neon_button import NeonButton
from .widgets.neon_checkbox import NeonCheckBox
from .widgets.neon_line_edit import NeonLineEdit
from .widgets.neon_progress_bar import NeonProgressBar


class ExportView(QWidget):
    """Export interface with channel selection, format options, and progress."""

    export_requested = Signal(list, list, str, str, bool)  # guild_ids, channel_ids, format, path, organize

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        title = GlowLabel("EXPORT MESSAGES", Colors.SUCCESS, font_size=18, glow_radius=10)
        layout.addWidget(title)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(16)

        # Left: Channel tree
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

        tree_title = QLabel("SELECT CHANNELS")
        tree_title.setStyleSheet(
            f"color: {Colors.SUCCESS}; font-size: 11px; letter-spacing: 2px; font-weight: bold;"
        )
        tree_layout.addWidget(tree_title)

        self._channel_tree = ChannelTree()
        tree_layout.addWidget(self._channel_tree)

        content.addWidget(tree_panel, 1)

        # Right: Options
        options_panel = QFrame()
        options_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        options_layout = QVBoxLayout(options_panel)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setSpacing(12)

        options_title = QLabel("OPTIONS")
        options_title.setStyleSheet(
            f"color: {Colors.SUCCESS}; font-size: 11px; letter-spacing: 2px; font-weight: bold;"
        )
        options_layout.addWidget(options_title)

        # Format selection
        format_label = QLabel("Export Format")
        format_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        options_layout.addWidget(format_label)

        self._json_radio = QRadioButton("JSON")
        self._json_radio.setChecked(True)
        self._csv_radio = QRadioButton("CSV")
        self._txt_radio = QRadioButton("TXT")

        format_row = QHBoxLayout()
        format_row.addWidget(self._json_radio)
        format_row.addWidget(self._csv_radio)
        format_row.addWidget(self._txt_radio)
        options_layout.addLayout(format_row)

        # Options
        self._organize_check = NeonCheckBox("Organize by channel folders", Colors.SUCCESS)
        self._organize_check.setChecked(True)
        options_layout.addWidget(self._organize_check)

        # Output directory
        dir_label = QLabel("Output Directory")
        dir_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        options_layout.addWidget(dir_label)

        dir_row = QHBoxLayout()
        self._dir_edit = NeonLineEdit(str(get_default_export_dir()))
        self._dir_edit.setText(str(get_default_export_dir()))
        dir_row.addWidget(self._dir_edit, 1)

        browse_btn = NeonButton("...", Colors.TEXT_SECONDARY)
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)
        options_layout.addLayout(dir_row)

        options_layout.addStretch()

        # Progress
        self._progress_bar = NeonProgressBar()
        options_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        options_layout.addWidget(self._status_label)

        # Export button
        self._export_btn = NeonButton("EXPORT", Colors.SUCCESS)
        self._export_btn.setMinimumHeight(40)
        self._export_btn.clicked.connect(self._on_export)
        options_layout.addWidget(self._export_btn)

        content.addWidget(options_panel, 1)
        layout.addLayout(content)

    @property
    def channel_tree(self) -> ChannelTree:
        return self._channel_tree

    def _get_format(self) -> str:
        if self._csv_radio.isChecked():
            return "csv"
        if self._txt_radio.isChecked():
            return "txt"
        return "json"

    def _browse_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", self._dir_edit.text()
        )
        if dir_path:
            self._dir_edit.setText(dir_path)

    def _on_export(self) -> None:
        guild_ids, channel_ids = self._channel_tree.get_selected()
        fmt = self._get_format()
        path = self._dir_edit.text()
        organize = self._organize_check.isChecked()
        self.export_requested.emit(guild_ids, channel_ids, fmt, path, organize)

    def set_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress_bar.set_max(total)
        self._progress_bar.set_value(current)
        self._status_label.setText(f"Exported {current} messages...")

    def set_complete(self, path: str) -> None:
        self._status_label.setText(f"Export complete: {path}")
        self._status_label.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 11px;")
        self._progress_bar.set_value(self._progress_bar._max_value)

    def set_running(self, running: bool) -> None:
        self._export_btn.setEnabled(not running)
        self._export_btn.setText("EXPORTING..." if running else "EXPORT")
