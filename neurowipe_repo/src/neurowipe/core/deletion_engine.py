"""Bulk message deletion engine with pause/resume/cancel."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Callable

from .discord_client import DiscordClient
from .exceptions import CancelledError, DeletionError, PausedError
from .models import DeletionJob, JobStatus, Message, SearchFilter
from .rate_limiter import RateLimiter
from .search_engine import SearchEngine

logger = logging.getLogger("neurowipe.deletion_engine")


class DeletionEngine:
    """Manages bulk deletion of Discord messages with pause/resume/cancel."""

    def __init__(
        self,
        client: DiscordClient,
        rate_limiter: RateLimiter,
        search_engine: SearchEngine,
    ):
        self.client = client
        self.rate_limiter = rate_limiter
        self.search_engine = search_engine
        self._paused = asyncio.Event()
        self._paused.set()  # Not paused initially
        self._cancelled = False
        self._current_job: DeletionJob | None = None
        self._on_progress: Callable[[DeletionJob], None] | None = None
        self._on_message_deleted: Callable[[Message, bool], None] | None = None
        self._on_log: Callable[[str, str], None] | None = None

    def set_callbacks(
        self,
        on_progress: Callable[[DeletionJob], None] | None = None,
        on_message_deleted: Callable[[Message, bool], None] | None = None,
        on_log: Callable[[str, str], None] | None = None,
    ) -> None:
        self._on_progress = on_progress
        self._on_message_deleted = on_message_deleted
        self._on_log = on_log

    def pause(self) -> None:
        logger.info("Deletion paused")
        self._paused.clear()
        if self._current_job:
            self._current_job.status = JobStatus.PAUSED
        self._log("WARNING", "Deletion paused by user")

    def resume(self) -> None:
        logger.info("Deletion resumed")
        self._paused.set()
        if self._current_job:
            self._current_job.status = JobStatus.RUNNING
        self._log("INFO", "Deletion resumed")

    def cancel(self) -> None:
        logger.info("Deletion cancelled")
        self._cancelled = True
        self._paused.set()  # Unpause so the loop can exit
        self.search_engine.cancel()
        if self._current_job:
            self._current_job.status = JobStatus.CANCELLED
        self._log("WARNING", "Deletion cancelled by user")

    @property
    def is_paused(self) -> bool:
        return not self._paused.is_set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def current_job(self) -> DeletionJob | None:
        return self._current_job

    def _log(self, level: str, message: str) -> None:
        if self._on_log:
            self._on_log(level, message)

    def _notify_progress(self) -> None:
        if self._on_progress and self._current_job:
            self._on_progress(self._current_job)

    async def scan(self, search_filter: SearchFilter) -> int:
        """Dry-run scan to count messages that would be deleted."""
        self._cancelled = False
        self.search_engine.reset()
        counts = await self.search_engine.count_messages(search_filter)
        total = sum(counts.values())
        logger.info(f"Scan complete: {total} messages found")
        return total

    async def execute(self, search_filter: SearchFilter) -> DeletionJob:
        """Execute bulk deletion."""
        self._cancelled = False
        self._paused.set()
        self.search_engine.reset()

        job = DeletionJob(
            status=JobStatus.RUNNING,
            filters=search_filter,
            started_at=datetime.now(),
        )
        self._current_job = job

        self._log("INFO", "Starting message scan...")

        # First count
        try:
            counts = await self.search_engine.count_messages(search_filter)
            job.total_messages = sum(counts.values())
            self._log("INFO", f"Found {job.total_messages} messages to delete")
            self._notify_progress()
        except CancelledError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            return job

        if job.total_messages == 0:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            self._log("INFO", "No messages found to delete")
            return job

        # Delete messages
        self._log("INFO", "Beginning deletion...")
        try:
            async for batch in self.search_engine.search_messages(search_filter):
                for message in batch:
                    # Check pause
                    await self._paused.wait()

                    # Check cancel
                    if self._cancelled:
                        raise CancelledError("Deletion cancelled")

                    # Delete
                    success = await self._delete_single(message)
                    if success:
                        job.deleted_count += 1
                    else:
                        job.failed_count += 1

                    self._notify_progress()

                    # Rate limit delay
                    await self.rate_limiter.wait_delete_delay()

        except CancelledError:
            job.status = JobStatus.CANCELLED
            self._log("WARNING", "Deletion cancelled")
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self._log("ERROR", f"Deletion failed: {e}")
            logger.exception("Deletion engine error")
        else:
            job.status = JobStatus.COMPLETED
            self._log(
                "INFO",
                f"Deletion complete: {job.deleted_count} deleted, "
                f"{job.failed_count} failed, {job.skipped_count} skipped",
            )

        job.completed_at = datetime.now()
        self._current_job = None
        self._notify_progress()
        return job

    async def _delete_single(self, message: Message) -> bool:
        """Delete a single message with retry logic."""
        for attempt in range(3):
            try:
                success = await self.client.delete_message(
                    message.channel_id, message.id
                )
                if self._on_message_deleted:
                    self._on_message_deleted(message, success)
                if success:
                    self._log(
                        "DEBUG",
                        f"Deleted message {message.id} in {message.channel_id}",
                    )
                else:
                    self._log(
                        "WARNING",
                        f"Failed to delete message {message.id}: forbidden",
                    )
                return success
            except DeletionError as e:
                if attempt < 2:
                    logger.warning(f"Delete retry {attempt + 1}: {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                self._log("ERROR", f"Failed to delete {message.id}: {e}")
                return False
            except Exception as e:
                self._log("ERROR", f"Unexpected error deleting {message.id}: {e}")
                return False
        return False
