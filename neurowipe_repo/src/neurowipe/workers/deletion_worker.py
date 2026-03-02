"""Worker for message deletion operations."""

from __future__ import annotations

from PySide6.QtCore import Signal

from ..core.deletion_engine import DeletionEngine
from ..core.models import DeletionJob, Message, SearchFilter
from .async_bridge import AsyncBridge
from .base_worker import BaseWorker


class DeletionWorker(BaseWorker):
    """Bridges DeletionEngine async operations to Qt signals."""

    job_progress = Signal(object)  # DeletionJob
    message_deleted = Signal(object, bool)  # Message, success
    job_complete = Signal(object)  # DeletionJob

    def __init__(self, bridge: AsyncBridge, deletion_engine: DeletionEngine, parent=None):
        super().__init__(parent)
        self._bridge = bridge
        self._engine = deletion_engine

        # Connect engine callbacks to signals
        self._engine.set_callbacks(
            on_progress=self._on_progress,
            on_message_deleted=self._on_message_deleted,
            on_log=self._on_log,
        )

    def start_deletion(self, search_filter: SearchFilter) -> None:
        """Start bulk deletion."""
        self.reset()
        self.started.emit()

        async def _do_delete():
            try:
                job = await self._engine.execute(search_filter)
                self.job_complete.emit(job)
            except Exception as e:
                self.error.emit(str(e))
            finally:
                self.finished.emit()

        self._bridge.submit(_do_delete())

    def pause(self) -> None:
        self._engine.pause()

    def resume(self) -> None:
        self._engine.resume()

    def cancel(self) -> None:
        super().cancel()
        self._engine.cancel()

    @property
    def is_paused(self) -> bool:
        return self._engine.is_paused

    @property
    def current_job(self) -> DeletionJob | None:
        return self._engine.current_job

    def _on_progress(self, job: DeletionJob) -> None:
        self.job_progress.emit(job)
        total = job.total_messages
        done = job.deleted_count + job.failed_count + job.skipped_count
        self.progress.emit(done, total)

    def _on_message_deleted(self, message: Message, success: bool) -> None:
        self.message_deleted.emit(message, success)

    def _on_log(self, level: str, message: str) -> None:
        self._emit_log(level, message)
