"""Reusable animation factories for cyberpunk UI effects."""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QTimer,
    Property,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


def create_fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """Create a fade-in animation for a widget."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
    return anim


def create_fade_out(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """Create a fade-out animation for a widget."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
    return anim


def create_glow_pulse(
    widget: QWidget,
    property_name: bytes = b"glow_intensity",
    min_val: float = 0.3,
    max_val: float = 1.0,
    duration: int = 1500,
) -> QSequentialAnimationGroup:
    """Create a pulsing glow animation."""
    group = QSequentialAnimationGroup(widget)

    fade_up = QPropertyAnimation(widget, property_name)
    fade_up.setDuration(duration // 2)
    fade_up.setStartValue(min_val)
    fade_up.setEndValue(max_val)
    fade_up.setEasingCurve(QEasingCurve.Type.InOutSine)

    fade_down = QPropertyAnimation(widget, property_name)
    fade_down.setDuration(duration // 2)
    fade_down.setStartValue(max_val)
    fade_down.setEndValue(min_val)
    fade_down.setEasingCurve(QEasingCurve.Type.InOutSine)

    group.addAnimation(fade_up)
    group.addAnimation(fade_down)
    group.setLoopCount(-1)  # Infinite loop
    return group


def create_slide_in(
    widget: QWidget,
    start_x: int = -50,
    end_x: int = 0,
    duration: int = 400,
) -> QPropertyAnimation:
    """Create a slide-in animation."""
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    pos = widget.pos()
    anim.setStartValue(pos.__class__(start_x, pos.y()))
    anim.setEndValue(pos.__class__(end_x, pos.y()))
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return anim


class FlickerEffect:
    """Creates a text flicker effect like a neon sign."""

    def __init__(self, widget: QWidget, interval_ms: int = 100):
        self._widget = widget
        self._timer = QTimer()
        self._timer.setInterval(interval_ms)
        self._step = 0
        self._pattern = [1.0, 0.7, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 0.8, 1.0]

        self._effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self._effect)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._effect.setOpacity(1.0)

    def _tick(self) -> None:
        opacity = self._pattern[self._step % len(self._pattern)]
        self._effect.setOpacity(opacity)
        self._step += 1
        if self._step >= len(self._pattern):
            self._step = 0
            self._timer.stop()
            # Restart after a random-ish delay
            QTimer.singleShot(3000, self.start)
