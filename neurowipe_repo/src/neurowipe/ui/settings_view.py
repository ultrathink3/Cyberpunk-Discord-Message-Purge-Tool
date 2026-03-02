"""SettingsView — Profiles, preferences, and app configuration."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.models import AppSettings, Profile
from ..theme.colors import Colors
from .widgets.glow_label import GlowLabel
from .widgets.neon_button import NeonButton
from .widgets.neon_checkbox import NeonCheckBox


class SettingsView(QWidget):
    """Settings view for profiles, deletion config, appearance, and data management."""

    settings_changed = Signal(object)  # AppSettings
    new_profile_requested = Signal()
    edit_profile_requested = Signal(int)  # profile_id
    delete_profile_requested = Signal(int)  # profile_id
    switch_profile_requested = Signal(int)  # profile_id
    clear_cache_requested = Signal()
    accent_color_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._profiles: list[Profile] = []
        self._settings = AppSettings()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        title = GlowLabel("SETTINGS", Colors.MAGENTA, font_size=18, glow_radius=10)
        layout.addWidget(title)

        # Profiles section
        profiles_group = QGroupBox("PROFILES")
        profiles_layout = QVBoxLayout(profiles_group)

        # Profile table
        self._profile_table = QTableWidget()
        self._profile_table.setColumnCount(4)
        self._profile_table.setHorizontalHeaderLabels(
            ["Active", "Username", "Name", "Actions"]
        )
        self._profile_table.verticalHeader().setVisible(False)
        self._profile_table.setMaximumHeight(180)
        header_view = self._profile_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        profiles_layout.addWidget(self._profile_table)

        profile_btns = QHBoxLayout()
        add_btn = NeonButton("+ New Profile", Colors.SUCCESS)
        add_btn.clicked.connect(self.new_profile_requested.emit)
        profile_btns.addWidget(add_btn)
        profile_btns.addStretch()
        profiles_layout.addLayout(profile_btns)

        layout.addWidget(profiles_group)

        # Two-column settings
        settings_row = QHBoxLayout()
        settings_row.setSpacing(16)

        # Deletion settings
        deletion_group = QGroupBox("DELETION")
        deletion_layout = QVBoxLayout(deletion_group)

        # Delay slider
        delay_label = QLabel("Delete Delay")
        delay_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        deletion_layout.addWidget(delay_label)

        delay_row = QHBoxLayout()
        self._delay_slider = QSlider(Qt.Orientation.Horizontal)
        self._delay_slider.setRange(200, 2000)
        self._delay_slider.setValue(400)
        self._delay_slider.setTickInterval(100)
        self._delay_slider.valueChanged.connect(self._on_delay_changed)
        delay_row.addWidget(self._delay_slider)

        self._delay_value_label = QLabel("0.4s")
        self._delay_value_label.setFixedWidth(40)
        self._delay_value_label.setStyleSheet(f"color: {Colors.CYAN};")
        delay_row.addWidget(self._delay_value_label)
        deletion_layout.addLayout(delay_row)

        # Retry count
        retry_row = QHBoxLayout()
        retry_label = QLabel("Max Retries")
        retry_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        retry_row.addWidget(retry_label)
        self._retry_spin = QSpinBox()
        self._retry_spin.setRange(1, 10)
        self._retry_spin.setValue(5)
        retry_row.addWidget(self._retry_spin)
        deletion_layout.addLayout(retry_row)

        # Confirm toggle
        self._confirm_check = NeonCheckBox("Confirm before delete", Colors.WARNING)
        self._confirm_check.setChecked(True)
        deletion_layout.addWidget(self._confirm_check)

        deletion_layout.addStretch()
        settings_row.addWidget(deletion_group)

        # Appearance settings
        appearance_group = QGroupBox("APPEARANCE")
        appearance_layout = QVBoxLayout(appearance_group)

        self._scanline_check = NeonCheckBox("CRT Scanline Effect", Colors.CYAN)
        self._scanline_check.setChecked(True)
        appearance_layout.addWidget(self._scanline_check)

        # Animation speed
        speed_row = QHBoxLayout()
        speed_label = QLabel("Animation Speed")
        speed_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        speed_row.addWidget(speed_label)
        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 3.0)
        self._speed_spin.setValue(1.0)
        self._speed_spin.setSingleStep(0.1)
        speed_row.addWidget(self._speed_spin)
        appearance_layout.addLayout(speed_row)

        # Accent color
        color_row = QHBoxLayout()
        color_label = QLabel("Accent Color")
        color_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        color_row.addWidget(color_label)

        self._color_btn = NeonButton("", Colors.CYAN)
        self._color_btn.setFixedSize(36, 36)
        self._color_btn.clicked.connect(self._pick_accent_color)
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        appearance_layout.addLayout(color_row)

        # Minimize to tray
        self._tray_check = NeonCheckBox("Minimize to tray on close", Colors.CYAN)
        self._tray_check.setChecked(True)
        appearance_layout.addWidget(self._tray_check)

        appearance_layout.addStretch()
        settings_row.addWidget(appearance_group)

        layout.addLayout(settings_row)

        # Data management
        data_row = QHBoxLayout()
        data_row.setSpacing(12)

        clear_cache_btn = NeonButton("Clear Cache", Colors.WARNING)
        clear_cache_btn.clicked.connect(self.clear_cache_requested.emit)
        data_row.addWidget(clear_cache_btn)

        data_row.addStretch()

        save_btn = NeonButton("SAVE SETTINGS", Colors.SUCCESS)
        save_btn.clicked.connect(self._save_settings)
        data_row.addWidget(save_btn)

        layout.addLayout(data_row)

    def set_profiles(self, profiles: list[Profile]) -> None:
        """Update the profiles table."""
        self._profiles = profiles
        self._profile_table.setRowCount(0)

        for profile in profiles:
            row = self._profile_table.rowCount()
            self._profile_table.insertRow(row)

            # Active indicator
            active_item = QTableWidgetItem("\u25cf" if profile.is_active else "")
            active_item.setForeground(
                QColor(Colors.SUCCESS if profile.is_active else Colors.TEXT_MUTED)
            )
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._profile_table.setItem(row, 0, active_item)

            # Username
            user_item = QTableWidgetItem(profile.username)
            user_item.setForeground(QColor(Colors.TEXT_PRIMARY))
            self._profile_table.setItem(row, 1, user_item)

            # Name
            name_item = QTableWidgetItem(profile.name)
            name_item.setForeground(QColor(Colors.TEXT_SECONDARY))
            self._profile_table.setItem(row, 2, name_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            switch_btn = NeonButton("\u25b6", Colors.CYAN)
            switch_btn.setFixedSize(28, 28)
            switch_btn.setToolTip("Switch to this profile")
            switch_btn.clicked.connect(
                lambda _, pid=profile.id: self.switch_profile_requested.emit(pid)
            )
            actions_layout.addWidget(switch_btn)

            edit_btn = NeonButton("\u270e", Colors.WARNING)
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Edit")
            edit_btn.clicked.connect(
                lambda _, pid=profile.id: self.edit_profile_requested.emit(pid)
            )
            actions_layout.addWidget(edit_btn)

            del_btn = NeonButton("\u2716", Colors.ERROR)
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip("Delete")
            del_btn.clicked.connect(
                lambda _, pid=profile.id: self.delete_profile_requested.emit(pid)
            )
            actions_layout.addWidget(del_btn)

            self._profile_table.setCellWidget(row, 3, actions_widget)

    def set_settings(self, settings: AppSettings) -> None:
        """Populate settings from AppSettings."""
        self._settings = settings
        self._delay_slider.setValue(int(settings.delete_delay * 1000))
        self._retry_spin.setValue(settings.retry_count)
        self._confirm_check.setChecked(settings.confirm_before_delete)
        self._scanline_check.setChecked(settings.scanline_enabled)
        self._speed_spin.setValue(settings.animation_speed)
        self._tray_check.setChecked(settings.minimize_to_tray)
        self._color_btn.set_color(settings.accent_color)

    def _on_delay_changed(self, value: int) -> None:
        self._delay_value_label.setText(f"{value / 1000:.1f}s")

    def _pick_accent_color(self) -> None:
        color = QColorDialog.getColor(
            QColor(self._settings.accent_color), self, "Select Accent Color"
        )
        if color.isValid():
            hex_color = color.name()
            self._color_btn.set_color(hex_color)
            self.accent_color_changed.emit(hex_color)

    def _save_settings(self) -> None:
        settings = AppSettings(
            delete_delay=self._delay_slider.value() / 1000,
            retry_count=self._retry_spin.value(),
            confirm_before_delete=self._confirm_check.isChecked(),
            scanline_enabled=self._scanline_check.isChecked(),
            animation_speed=self._speed_spin.value(),
            accent_color=self._settings.accent_color,
            minimize_to_tray=self._tray_check.isChecked(),
        )
        self.settings_changed.emit(settings)
