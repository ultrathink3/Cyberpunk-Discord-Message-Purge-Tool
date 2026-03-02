"""ProfileEditorDialog — Create/edit Discord account profiles."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from ...core.models import Profile
from ...theme.colors import Colors
from ..widgets.glow_label import GlowLabel
from ..widgets.neon_button import NeonButton
from ..widgets.neon_line_edit import NeonLineEdit


class ProfileEditorDialog(QDialog):
    """Dialog for creating or editing a profile."""

    def __init__(self, profile: Profile | None = None, parent=None):
        super().__init__(parent)
        self._profile = profile
        self._is_edit = profile is not None

        self.setWindowTitle("Edit Profile" if self._is_edit else "New Profile")
        self.setFixedSize(440, 300)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.CYAN};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title_text = "EDIT PROFILE" if self._is_edit else "NEW PROFILE"
        title = GlowLabel(title_text, color=Colors.CYAN, font_size=16, glow_radius=10)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Profile name
        name_label = QLabel("Profile Name")
        name_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(name_label)

        self._name_edit = NeonLineEdit("Enter a name for this profile")
        if self._is_edit and profile:
            self._name_edit.setText(profile.name)
        layout.addWidget(self._name_edit)

        # Token
        token_label = QLabel("Discord Token")
        token_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(token_label)

        self._token_edit = NeonLineEdit("Paste your Discord token")
        self._token_edit.setEchoMode(NeonLineEdit.EchoMode.Password)
        layout.addWidget(self._token_edit)

        if self._is_edit:
            self._token_edit.setPlaceholderText("Leave empty to keep current token")

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = NeonButton("CANCEL", Colors.TEXT_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = NeonButton(
            "SAVE" if self._is_edit else "CREATE",
            Colors.SUCCESS,
        )
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    @property
    def profile_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def token(self) -> str:
        return self._token_edit.text().strip()
