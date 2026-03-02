"""SQLite database for local persistence with schema migrations."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from ..constants import DB_FILENAME, DB_VERSION
from ..utils.platform_utils import get_data_dir
from .exceptions import DatabaseError
from .models import AppSettings, DeletionJob, JobStatus, Profile, ScheduledJob

logger = logging.getLogger("neurowipe.database")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL DEFAULT '',
    discriminator TEXT NOT NULL DEFAULT '0',
    avatar TEXT,
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_used TEXT
);

CREATE TABLE IF NOT EXISTS deletion_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER REFERENCES profiles(id),
    status TEXT NOT NULL DEFAULT 'pending',
    total_messages INTEGER NOT NULL DEFAULT 0,
    deleted_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    filters_json TEXT,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER REFERENCES profiles(id),
    name TEXT NOT NULL,
    cron_expression TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    guild_ids_json TEXT DEFAULT '[]',
    channel_ids_json TEXT DEFAULT '[]',
    filters_json TEXT,
    last_run TEXT,
    next_run TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (get_data_dir() / DB_FILENAME)
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open database connection and initialize schema."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.executescript(SCHEMA_SQL)

        # Set schema version
        async with self._db.execute("SELECT version FROM schema_version") as cursor:
            row = await cursor.fetchone()
            if not row:
                await self._db.execute(
                    "INSERT INTO schema_version (version) VALUES (?)", (DB_VERSION,)
                )

        await self._db.commit()
        logger.info(f"Database connected: {self.db_path}")

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if not self._db:
            raise DatabaseError("Database not connected")
        return self._db

    # --- Profiles ---

    async def get_profiles(self) -> list[Profile]:
        async with self.db.execute("SELECT * FROM profiles ORDER BY name") as cursor:
            rows = await cursor.fetchall()
        return [self._row_to_profile(r) for r in rows]

    async def get_active_profile(self) -> Profile | None:
        async with self.db.execute(
            "SELECT * FROM profiles WHERE is_active = 1 LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
        return self._row_to_profile(row) if row else None

    async def create_profile(self, profile: Profile) -> int:
        cursor = await self.db.execute(
            """INSERT INTO profiles (name, user_id, username, discriminator, avatar, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                profile.name,
                profile.user_id,
                profile.username,
                profile.discriminator,
                profile.avatar,
                1 if profile.is_active else 0,
            ),
        )
        await self.db.commit()
        return cursor.lastrowid

    async def update_profile(self, profile: Profile) -> None:
        await self.db.execute(
            """UPDATE profiles SET name=?, user_id=?, username=?, discriminator=?,
               avatar=?, is_active=?, last_used=? WHERE id=?""",
            (
                profile.name,
                profile.user_id,
                profile.username,
                profile.discriminator,
                profile.avatar,
                1 if profile.is_active else 0,
                profile.last_used.isoformat() if profile.last_used else None,
                profile.id,
            ),
        )
        await self.db.commit()

    async def delete_profile(self, profile_id: int) -> None:
        await self.db.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
        await self.db.commit()

    async def set_active_profile(self, profile_id: int) -> None:
        await self.db.execute("UPDATE profiles SET is_active = 0")
        await self.db.execute(
            "UPDATE profiles SET is_active = 1 WHERE id = ?", (profile_id,)
        )
        await self.db.commit()

    def _row_to_profile(self, row) -> Profile:
        return Profile(
            id=row["id"],
            name=row["name"],
            user_id=row["user_id"],
            username=row["username"],
            discriminator=row["discriminator"],
            avatar=row["avatar"],
            is_active=bool(row["is_active"]),
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else None
            ),
            last_used=(
                datetime.fromisoformat(row["last_used"])
                if row["last_used"]
                else None
            ),
        )

    # --- Deletion Jobs ---

    async def save_deletion_job(self, job: DeletionJob) -> int:
        if job.id:
            await self.db.execute(
                """UPDATE deletion_jobs SET status=?, total_messages=?, deleted_count=?,
                   failed_count=?, skipped_count=?, started_at=?, completed_at=?, error_message=?
                   WHERE id=?""",
                (
                    job.status.value,
                    job.total_messages,
                    job.deleted_count,
                    job.failed_count,
                    job.skipped_count,
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.error_message,
                    job.id,
                ),
            )
            await self.db.commit()
            return job.id
        else:
            cursor = await self.db.execute(
                """INSERT INTO deletion_jobs (profile_id, status, total_messages, deleted_count,
                   failed_count, skipped_count, started_at, completed_at, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job.profile_id,
                    job.status.value,
                    job.total_messages,
                    job.deleted_count,
                    job.failed_count,
                    job.skipped_count,
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    job.error_message,
                ),
            )
            await self.db.commit()
            return cursor.lastrowid

    async def get_deletion_jobs(self, profile_id: int | None = None) -> list[DeletionJob]:
        if profile_id:
            query = "SELECT * FROM deletion_jobs WHERE profile_id=? ORDER BY id DESC"
            params = (profile_id,)
        else:
            query = "SELECT * FROM deletion_jobs ORDER BY id DESC"
            params = ()
        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
        return [self._row_to_job(r) for r in rows]

    def _row_to_job(self, row) -> DeletionJob:
        return DeletionJob(
            id=row["id"],
            profile_id=row["profile_id"],
            status=JobStatus(row["status"]),
            total_messages=row["total_messages"],
            deleted_count=row["deleted_count"],
            failed_count=row["failed_count"],
            skipped_count=row["skipped_count"],
            started_at=(
                datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            error_message=row["error_message"],
        )

    # --- Scheduled Jobs ---

    async def get_scheduled_jobs(self, profile_id: int | None = None) -> list[ScheduledJob]:
        if profile_id:
            query = "SELECT * FROM scheduled_jobs WHERE profile_id=? ORDER BY name"
            params = (profile_id,)
        else:
            query = "SELECT * FROM scheduled_jobs ORDER BY name"
            params = ()
        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
        return [self._row_to_scheduled(r) for r in rows]

    async def save_scheduled_job(self, job: ScheduledJob) -> int:
        if job.id:
            await self.db.execute(
                """UPDATE scheduled_jobs SET name=?, cron_expression=?, enabled=?,
                   guild_ids_json=?, channel_ids_json=?, filters_json=?,
                   last_run=?, next_run=? WHERE id=?""",
                (
                    job.name,
                    job.cron_expression,
                    1 if job.enabled else 0,
                    json.dumps(job.guild_ids),
                    json.dumps(job.channel_ids),
                    None,
                    job.last_run.isoformat() if job.last_run else None,
                    job.next_run.isoformat() if job.next_run else None,
                    job.id,
                ),
            )
            await self.db.commit()
            return job.id
        else:
            cursor = await self.db.execute(
                """INSERT INTO scheduled_jobs (profile_id, name, cron_expression, enabled,
                   guild_ids_json, channel_ids_json, filters_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    job.profile_id,
                    job.name,
                    job.cron_expression,
                    1 if job.enabled else 0,
                    json.dumps(job.guild_ids),
                    json.dumps(job.channel_ids),
                    None,
                ),
            )
            await self.db.commit()
            return cursor.lastrowid

    async def delete_scheduled_job(self, job_id: int) -> None:
        await self.db.execute("DELETE FROM scheduled_jobs WHERE id=?", (job_id,))
        await self.db.commit()

    def _row_to_scheduled(self, row) -> ScheduledJob:
        return ScheduledJob(
            id=row["id"],
            profile_id=row["profile_id"],
            name=row["name"],
            cron_expression=row["cron_expression"],
            enabled=bool(row["enabled"]),
            guild_ids=json.loads(row["guild_ids_json"] or "[]"),
            channel_ids=json.loads(row["channel_ids_json"] or "[]"),
            last_run=(
                datetime.fromisoformat(row["last_run"]) if row["last_run"] else None
            ),
            next_run=(
                datetime.fromisoformat(row["next_run"]) if row["next_run"] else None
            ),
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else None
            ),
        )

    # --- Settings ---

    async def get_setting(self, key: str, default: str = "") -> str:
        async with self.db.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await self.db.commit()

    async def get_all_settings(self) -> AppSettings:
        settings = AppSettings()
        settings.delete_delay = float(
            await self.get_setting("delete_delay", str(settings.delete_delay))
        )
        settings.retry_count = int(
            await self.get_setting("retry_count", str(settings.retry_count))
        )
        settings.confirm_before_delete = (
            await self.get_setting("confirm_before_delete", "1")
        ) == "1"
        settings.scanline_enabled = (
            await self.get_setting("scanline_enabled", "1")
        ) == "1"
        settings.animation_speed = float(
            await self.get_setting("animation_speed", str(settings.animation_speed))
        )
        settings.accent_color = await self.get_setting(
            "accent_color", settings.accent_color
        )
        settings.minimize_to_tray = (
            await self.get_setting("minimize_to_tray", "1")
        ) == "1"
        return settings

    async def save_all_settings(self, settings: AppSettings) -> None:
        await self.set_setting("delete_delay", str(settings.delete_delay))
        await self.set_setting("retry_count", str(settings.retry_count))
        await self.set_setting(
            "confirm_before_delete", "1" if settings.confirm_before_delete else "0"
        )
        await self.set_setting(
            "scanline_enabled", "1" if settings.scanline_enabled else "0"
        )
        await self.set_setting("animation_speed", str(settings.animation_speed))
        await self.set_setting("accent_color", settings.accent_color)
        await self.set_setting(
            "minimize_to_tray", "1" if settings.minimize_to_tray else "0"
        )
