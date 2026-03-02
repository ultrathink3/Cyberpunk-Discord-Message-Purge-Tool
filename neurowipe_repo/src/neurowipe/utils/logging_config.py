"""Logging configuration for NEUROWIPE."""

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from ..constants import LOG_FORMAT, LOG_DATE_FORMAT


class SignalHandler(logging.Handler, QObject):
    """Logging handler that emits Qt signals for log messages."""

    log_message = Signal(str, str)  # level, message

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_message.emit(record.levelname, msg)
        except Exception:
            self.handleError(record)


_signal_handler: SignalHandler | None = None


def get_signal_handler() -> SignalHandler:
    """Get or create the global signal handler."""
    global _signal_handler
    if _signal_handler is None:
        _signal_handler = SignalHandler()
    return _signal_handler


def setup_logging(log_dir: Path | None = None, debug: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger("neurowipe")
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_dir:
        log_file = log_dir / "neurowipe.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Signal handler for GUI log panel
    signal_handler = get_signal_handler()
    signal_handler.setLevel(level)
    root_logger.addHandler(signal_handler)

    root_logger.info("NEUROWIPE logging initialized")
