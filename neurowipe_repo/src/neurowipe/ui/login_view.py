"""LoginView — Token entry and profile selector."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.models import Profile
from ..theme.colors import Colors
from .widgets.animated_logo import AnimatedLogo
from .widgets.glow_label import GlowLabel
from .widgets.neon_button import NeonButton
from .widgets.neon_combo_box import NeonComboBox
from .widgets.neon_line_edit import NeonLineEdit


class LoginView(QWidget):
    """Login screen with token entry, profile selector, and animated logo."""

    connect_requested = Signal(str)  # token
    profile_connect_requested = Signal(int)  # profile_id
    new_profile_requested = Signal()
    edit_profile_requested = Signal(int)  # profile_id
    delete_profile_requested = Signal(int)  # profile_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._profiles: list[Profile] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        layout.addStretch(2)

        # Animated logo
        self._logo = AnimatedLogo()
        layout.addWidget(self._logo, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(24)

        # Center container (fixed width)
        center = QWidget()
        center.setFixedWidth(400)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)

        # Profile selector
        profile_label = QLabel("PROFILE")
        profile_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; letter-spacing: 2px;"
        )
        center_layout.addWidget(profile_label)

        profile_row = QHBoxLayout()
        profile_row.setSpacing(8)

        self._profile_combo = NeonComboBox()
        self._profile_combo.addItem("-- Direct Token --")
        profile_row.addWidget(self._profile_combo, 1)

        self._new_profile_btn = QPushButton("+")
        self._new_profile_btn.setFixedSize(36, 36)
        self._new_profile_btn.setToolTip("New Profile")
        self._new_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.SUCCESS};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {Colors.SUCCESS};
            }}
        """)
        self._new_profile_btn.clicked.connect(self.new_profile_requested.emit)
        profile_row.addWidget(self._new_profile_btn)

        self._edit_profile_btn = QPushButton("\u270e")
        self._edit_profile_btn.setFixedSize(36, 36)
        self._edit_profile_btn.setToolTip("Edit Profile")
        self._edit_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.WARNING};
                font-size: 14px;
            }}
            QPushButton:hover {{
                border-color: {Colors.WARNING};
            }}
        """)
        self._edit_profile_btn.clicked.connect(self._on_edit_profile)
        profile_row.addWidget(self._edit_profile_btn)

        self._delete_profile_btn = QPushButton("\u2716")
        self._delete_profile_btn.setFixedSize(36, 36)
        self._delete_profile_btn.setToolTip("Delete Profile")
        self._delete_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.ERROR};
                font-size: 14px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ERROR};
            }}
        """)
        self._delete_profile_btn.clicked.connect(self._on_delete_profile)
        profile_row.addWidget(self._delete_profile_btn)

        center_layout.addLayout(profile_row)

        # Token input
        token_label = QLabel("TOKEN")
        token_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; letter-spacing: 2px;"
        )
        center_layout.addWidget(token_label)

        token_row = QHBoxLayout()
        self._token_edit = NeonLineEdit("Paste your Discord token here")
        self._token_edit.setEchoMode(NeonLineEdit.EchoMode.Password)
        token_row.addWidget(self._token_edit, 1)

        self._show_token_btn = QPushButton("\u25cf")
        self._show_token_btn.setFixedSize(36, 36)
        self._show_token_btn.setCheckable(True)
        self._show_token_btn.setToolTip("Show/Hide Token")
        self._show_token_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_MUTED};
                font-size: 14px;
            }}
            QPushButton:checked {{
                color: {Colors.CYAN};
                border-color: {Colors.CYAN};
            }}
        """)
        self._show_token_btn.toggled.connect(self._toggle_token_visibility)
        token_row.addWidget(self._show_token_btn)

        center_layout.addLayout(token_row)

        center_layout.addSpacing(8)

        # Connect button
        self._connect_btn = NeonButton("CONNECT", Colors.CYAN)
        self._connect_btn.setMinimumHeight(44)
        self._connect_btn.clicked.connect(self._on_connect)
        center_layout.addWidget(self._connect_btn)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        center_layout.addWidget(self._status_label)

        layout.addWidget(center, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(3)

    def start_animations(self) -> None:
        self._logo.start_animation()

    def stop_animations(self) -> None:
        self._logo.stop_animation()

    def set_profiles(self, profiles: list[Profile]) -> None:
        """Update the profile dropdown."""
        self._profiles = profiles
        self._profile_combo.clear()
        self._profile_combo.addItem("-- Direct Token --")
        for p in profiles:
            label = f"{p.name} ({p.username})"
            if p.is_active:
                label += " \u2713"
            self._profile_combo.addItem(label, p.id)

    def set_status(self, message: str, error: bool = False) -> None:
        color = Colors.ERROR if error else Colors.TEXT_SECONDARY
        self._status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._status_label.setText(message)

    def set_connecting(self, connecting: bool) -> None:
        self._connect_btn.setEnabled(not connecting)
        self._connect_btn.setText("CONNECTING..." if connecting else "CONNECT")

    def _on_connect(self) -> None:
        idx = self._profile_combo.currentIndex()
        if idx > 0 and idx - 1 < len(self._profiles):
            profile = self._profiles[idx - 1]
            self.profile_connect_requested.emit(profile.id)
        else:
            token = self._token_edit.text().strip()
            if token:
                self.connect_requested.emit(token)
            else:
                self.set_status("Please enter a token or select a profile", error=True)

    def _on_edit_profile(self) -> None:
        idx = self._profile_combo.currentIndex()
        if idx > 0 and idx - 1 < len(self._profiles):
            self.edit_profile_requested.emit(self._profiles[idx - 1].id)

    def _on_delete_profile(self) -> None:
        idx = self._profile_combo.currentIndex()
        if idx > 0 and idx - 1 < len(self._profiles):
            self.delete_profile_requested.emit(self._profiles[idx - 1].id)

    def _toggle_token_visibility(self, checked: bool) -> None:
        self._token_edit.setEchoMode(
            NeonLineEdit.EchoMode.Normal if checked else NeonLineEdit.EchoMode.Password
        )
