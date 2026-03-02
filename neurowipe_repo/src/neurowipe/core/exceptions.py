"""Custom exception classes for NEUROWIPE."""


class NeurowipeError(Exception):
    """Base exception for all NEUROWIPE errors."""


class TokenError(NeurowipeError):
    """Invalid or expired Discord token."""


class RateLimitError(NeurowipeError):
    """Rate limited by Discord API."""

    def __init__(self, retry_after: float, message: str = "Rate limited"):
        self.retry_after = retry_after
        super().__init__(f"{message} (retry after {retry_after:.2f}s)")


class SearchError(NeurowipeError):
    """Error during message search."""


class DeletionError(NeurowipeError):
    """Error during message deletion."""


class ExportError(NeurowipeError):
    """Error during message export."""


class DatabaseError(NeurowipeError):
    """Database operation error."""


class VaultError(NeurowipeError):
    """Token vault / encryption error."""


class ProfileError(NeurowipeError):
    """Profile management error."""


class SchedulerError(NeurowipeError):
    """Scheduler operation error."""


class CancelledError(NeurowipeError):
    """Operation was cancelled by user."""


class PausedError(NeurowipeError):
    """Operation is paused."""
