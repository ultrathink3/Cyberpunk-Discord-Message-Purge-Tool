"""AnimatedLogo — Animated NEUROWIPE title with flicker effect."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...constants import APP_NAME, APP_TAGLINE
from ...theme.colors import Colors
from ...theme.fonts import get_logo_font


class AnimatedLogo(QWidget):
    """Animated NEUROWIPE logo with glow and flicker effects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._flicker_step = 0
        self._flicker_pattern = [1.0, 0.7, 1.0, 1.0, 0.4, 1.0, 1.0, 1.0, 0.8, 1.0]

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Logo text
        self._logo_label = QLabel(APP_NAME)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_font = get_logo_font(32)
        self._logo_label.setFont(logo_font)
        self._logo_label.setStyleSheet(f"""
            color: {Colors.CYAN};
            background: transparent;
            letter-spacing: 6px;
        """)

        # Logo glow
        self._logo_shadow = QGraphicsDropShadowEffect(self._logo_label)
        self._logo_shadow.setBlurRadius(25)
        self._logo_shadow.setColor(QColor(Colors.CYAN))
        self._logo_shadow.setOffset(0, 0)
        self._logo_label.setGraphicsEffect(self._logo_shadow)

        # Tagline
        self._tagline_label = QLabel(f'"{APP_TAGLINE}"')
        self._tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tagline_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background: transparent;
            font-size: 12px;
            font-style: italic;
        """)

        layout.addWidget(self._logo_label)
        layout.addWidget(self._tagline_label)

        # Flicker timer
        self._flicker_timer = QTimer(self)
        self._flicker_timer.setInterval(80)
        self._flicker_timer.timeout.connect(self._do_flicker)

        # Glow pulse
        self._glow_value = 25.0
        self._glow_anim = QPropertyAnimation(self, b"glow_value")
        self._glow_anim.setDuration(3000)
        self._glow_anim.setStartValue(15.0)
        self._glow_anim.setEndValue(35.0)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._glow_anim.setLoopCount(-1)

    @Property(float)
    def glow_value(self) -> float:
        return self._glow_value

    @glow_value.setter
    def glow_value(self, val: float) -> None:
        self._glow_value = val
        self._logo_shadow.setBlurRadius(val)

    def start_animation(self) -> None:
        """Start the logo animations."""
        self._glow_anim.start()
        # Trigger flicker periodically
        QTimer.singleShot(2000, self._start_flicker)

    def stop_animation(self) -> None:
        """Stop all animations."""
        self._glow_anim.stop()
        self._flicker_timer.stop()

    def _start_flicker(self) -> None:
        self._flicker_step = 0
        self._flicker_timer.start()

    def _do_flicker(self) -> None:
        if self._flicker_step >= len(self._flicker_pattern):
            self._flicker_timer.stop()
            self._logo_label.setStyleSheet(f"""
                color: {Colors.CYAN};
                background: transparent;
                letter-spacing: 6px;
            """)
            # Schedule next flicker
            QTimer.singleShot(5000, self._start_flicker)
            return

        opacity = self._flicker_pattern[self._flicker_step]
        r, g, b = Colors.to_rgb_tuple(Colors.CYAN)
        self._logo_label.setStyleSheet(f"""
            color: rgba({r}, {g}, {b}, {opacity});
            background: transparent;
            letter-spacing: 6px;
        """)
        self._flicker_step += 1
