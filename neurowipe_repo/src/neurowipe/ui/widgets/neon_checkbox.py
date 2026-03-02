"""NeonCheckBox — Checkbox with neon accent."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox

from ...theme.colors import Colors


class NeonCheckBox(QCheckBox):
    """Checkbox with cyberpunk neon styling."""

    def __init__(self, text: str = "", color: str = Colors.CYAN, parent=None):
        super().__init__(text, parent)
        self._color = color
        self._apply_style()

    def _apply_style(self) -> None:
        r, g, b = Colors.to_rgb_tuple(self._color)
        self.setStyleSheet(f"""
            NeonCheckBox {{
                spacing: 8px;
                color: {Colors.TEXT_PRIMARY};
            }}
            NeonCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {Colors.BORDER_FOCUS};
                border-radius: 4px;
                background-color: {Colors.BG_INPUT};
            }}
            NeonCheckBox::indicator:hover {{
                border-color: {self._color};
            }}
            NeonCheckBox::indicator:checked {{
                background-color: rgba({r}, {g}, {b}, 0.3);
                border-color: {self._color};
            }}
        """)

    def set_color(self, color: str) -> None:
        self._color = color
        self._apply_style()
