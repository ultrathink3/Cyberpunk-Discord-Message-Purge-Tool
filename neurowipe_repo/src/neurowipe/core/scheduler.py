"""Scheduled job management using APScheduler."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import Database
from .exceptions import SchedulerError
from .models import ScheduledJob, SearchFilter

logger = logging.getLogger("neurowipe.scheduler")


class SchedulerManager:
    """Manages scheduled deletion jobs using APScheduler."""

    def __init__(self, database: Database):
        self.database = database
        self._scheduler = AsyncIOScheduler()
        self._job_callback: Callable[[ScheduledJob], None] | None = None
        self._running = False

    def set_job_callback(self, callback: Callable[[ScheduledJob], None]) -> None:
        """Set callback to invoke when a scheduled job fires."""
        self._job_callback = callback

    async def start(self) -> None:
        """Start the scheduler and load persisted jobs."""
        if self._running:
            return

        jobs = await self.database.get_scheduled_jobs()
        for job in jobs:
            if job.enabled:
                self._add_apscheduler_job(job)

        self._scheduler.start()
        self._running = True
        logger.info(f"Scheduler started with {len(jobs)} jobs")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped")

    async def add_job(self, job: ScheduledJob) -> ScheduledJob:
        """Add a new scheduled job."""
        job.id = await self.database.save_scheduled_job(job)

        if job.enabled:
            self._add_apscheduler_job(job)

        logger.info(f"Scheduled job added: {job.name} ({job.cron_expression})")
        return job

    async def update_job(self, job: ScheduledJob) -> None:
        """Update an existing scheduled job."""
        await self.database.save_scheduled_job(job)

        # Remove and re-add to APScheduler
        ap_job_id = f"neurowipe_job_{job.id}"
        try:
            self._scheduler.remove_job(ap_job_id)
        except Exception:
            pass

        if job.enabled:
            self._add_apscheduler_job(job)

        logger.info(f"Scheduled job updated: {job.name}")

    async def remove_job(self, job_id: int) -> None:
        """Remove a scheduled job."""
        ap_job_id = f"neurowipe_job_{job_id}"
        try:
            self._scheduler.remove_job(ap_job_id)
        except Exception:
            pass
        await self.database.delete_scheduled_job(job_id)
        logger.info(f"Scheduled job removed: {job_id}")

    async def toggle_job(self, job_id: int, enabled: bool) -> None:
        """Enable or disable a scheduled job."""
        jobs = await self.database.get_scheduled_jobs()
        job = next((j for j in jobs if j.id == job_id), None)
        if not job:
            raise SchedulerError(f"Job {job_id} not found")

        job.enabled = enabled
        await self.database.save_scheduled_job(job)

        ap_job_id = f"neurowipe_job_{job_id}"
        if enabled:
            self._add_apscheduler_job(job)
        else:
            try:
                self._scheduler.remove_job(ap_job_id)
            except Exception:
                pass

    async def run_now(self, job_id: int) -> None:
        """Trigger a scheduled job immediately."""
        jobs = await self.database.get_scheduled_jobs()
        job = next((j for j in jobs if j.id == job_id), None)
        if not job:
            raise SchedulerError(f"Job {job_id} not found")

        await self._execute_job(job)

    def _add_apscheduler_job(self, job: ScheduledJob) -> None:
        """Add a job to APScheduler from our model."""
        ap_job_id = f"neurowipe_job_{job.id}"
        try:
            parts = job.cron_expression.split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                )
                self._scheduler.add_job(
                    self._execute_job,
                    trigger=trigger,
                    args=[job],
                    id=ap_job_id,
                    replace_existing=True,
                    name=job.name,
                )
                # Update next run time
                next_fire = trigger.get_next_fire_time(None, datetime.now())
                if next_fire:
                    job.next_run = next_fire
        except Exception as e:
            logger.error(f"Failed to schedule job {job.name}: {e}")

    async def _execute_job(self, job: ScheduledJob) -> None:
        """Execute a scheduled job."""
        logger.info(f"Executing scheduled job: {job.name}")
        job.last_run = datetime.now()
        await self.database.save_scheduled_job(job)

        if self._job_callback:
            self._job_callback(job)

    async def get_jobs(self) -> list[ScheduledJob]:
        """Get all scheduled jobs."""
        return await self.database.get_scheduled_jobs()
