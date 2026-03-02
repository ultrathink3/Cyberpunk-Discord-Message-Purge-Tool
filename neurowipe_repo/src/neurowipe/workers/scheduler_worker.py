"""Worker for scheduler management."""

from __future__ import annotations

from PySide6.QtCore import Signal

from ..core.models import ScheduledJob
from ..core.scheduler import SchedulerManager
from .async_bridge import AsyncBridge
from .base_worker import BaseWorker


class SchedulerWorker(BaseWorker):
    """Bridges SchedulerManager operations to Qt signals."""

    jobs_loaded = Signal(list)  # list[ScheduledJob]
    job_added = Signal(object)  # ScheduledJob
    job_fired = Signal(object)  # ScheduledJob
    scheduler_started = Signal()

    def __init__(self, bridge: AsyncBridge, scheduler: SchedulerManager, parent=None):
        super().__init__(parent)
        self._bridge = bridge
        self._scheduler = scheduler

        # Set callback for when a scheduled job fires
        self._scheduler.set_job_callback(self._on_job_fired)

    def start_scheduler(self) -> None:
        """Start the scheduler."""
        self.started.emit()

        async def _do_start():
            try:
                await self._scheduler.start()
                self.scheduler_started.emit()
                self._emit_log("INFO", "Scheduler started")
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_start())

    def stop_scheduler(self) -> None:
        """Stop the scheduler."""
        self._scheduler.stop()
        self._emit_log("INFO", "Scheduler stopped")

    def load_jobs(self) -> None:
        """Load all scheduled jobs."""
        async def _do_load():
            try:
                jobs = await self._scheduler.get_jobs()
                self.jobs_loaded.emit(jobs)
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_load())

    def add_job(self, job: ScheduledJob) -> None:
        """Add a new scheduled job."""
        async def _do_add():
            try:
                result = await self._scheduler.add_job(job)
                self.job_added.emit(result)
                self._emit_log("INFO", f"Job added: {result.name}")
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_add())

    def update_job(self, job: ScheduledJob) -> None:
        """Update a scheduled job."""
        async def _do_update():
            try:
                await self._scheduler.update_job(job)
                self._emit_log("INFO", f"Job updated: {job.name}")
                self.load_jobs()
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_update())

    def remove_job(self, job_id: int) -> None:
        """Remove a scheduled job."""
        async def _do_remove():
            try:
                await self._scheduler.remove_job(job_id)
                self._emit_log("INFO", f"Job removed: {job_id}")
                self.load_jobs()
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_remove())

    def toggle_job(self, job_id: int, enabled: bool) -> None:
        """Toggle a scheduled job."""
        async def _do_toggle():
            try:
                await self._scheduler.toggle_job(job_id, enabled)
                self.load_jobs()
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_toggle())

    def run_now(self, job_id: int) -> None:
        """Run a scheduled job immediately."""
        async def _do_run():
            try:
                await self._scheduler.run_now(job_id)
                self.load_jobs()
            except Exception as e:
                self.error.emit(str(e))

        self._bridge.submit(_do_run())

    def _on_job_fired(self, job: ScheduledJob) -> None:
        self.job_fired.emit(job)
        self._emit_log("INFO", f"Scheduled job fired: {job.name}")
