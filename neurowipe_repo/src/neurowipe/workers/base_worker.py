"""Abstract base worker with standard Qt signals."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class BaseWorker(QObject):
    """Base class for workers that bridge async operations to Qt signals."""

    # Common signals
    started = Signal()
    finished = Signal()
    error = Signal(str)
    progress = Signal(int, int)  # current, total
    log_message = Signal(str, str)  # level, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def reset(self) -> None:
        """Reset cancellation state."""
        self._cancelled = False

    def _emit_log(self, level: str, message: str) -> None:
        """Emit a log message signal."""
        self.log_message.emit(level, message)
