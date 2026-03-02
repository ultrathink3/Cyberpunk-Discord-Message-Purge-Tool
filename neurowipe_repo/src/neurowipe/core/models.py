"""Data models for NEUROWIPE."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ExportFormat(enum.Enum):
    JSON = "json"
    CSV = "csv"
    TXT = "txt"


class ChannelType(enum.Enum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_ANNOUNCEMENT = 5
    GUILD_FORUM = 15
    GUILD_MEDIA = 16


@dataclass
class UserInfo:
    id: str
    username: str
    discriminator: str
    avatar: Optional[str] = None
    global_name: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.global_name:
            return self.global_name
        if self.discriminator and self.discriminator != "0":
            return f"{self.username}#{self.discriminator}"
        return self.username

    @classmethod
    def from_dict(cls, data: dict) -> UserInfo:
        return cls(
            id=data["id"],
            username=data["username"],
            discriminator=data.get("discriminator", "0"),
            avatar=data.get("avatar"),
            global_name=data.get("global_name"),
        )


@dataclass
class Guild:
    id: str
    name: str
    icon: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Guild:
        return cls(id=data["id"], name=data["name"], icon=data.get("icon"))


@dataclass
class Channel:
    id: str
    name: str
    type: ChannelType
    guild_id: Optional[str] = None
    parent_id: Optional[str] = None
    position: int = 0
    recipients: list[str] = field(default_factory=list)

    @property
    def is_text(self) -> bool:
        return self.type in (
            ChannelType.GUILD_TEXT,
            ChannelType.DM,
            ChannelType.GROUP_DM,
            ChannelType.GUILD_ANNOUNCEMENT,
            ChannelType.GUILD_FORUM,
        )

    @classmethod
    def from_dict(cls, data: dict) -> Channel:
        recipients = []
        if "recipients" in data:
            recipients = [r.get("username", "Unknown") for r in data["recipients"]]
        ch_type = data.get("type", 0)
        name = data.get("name") or ""
        if ch_type == 1 and recipients:
            name = recipients[0]
        elif ch_type == 3 and recipients:
            name = name or ", ".join(recipients[:3])
        return cls(
            id=data["id"],
            name=name,
            type=ChannelType(ch_type) if ch_type in [e.value for e in ChannelType] else ChannelType.GUILD_TEXT,
            guild_id=data.get("guild_id"),
            parent_id=data.get("parent_id"),
            position=data.get("position", 0),
            recipients=recipients,
        )


@dataclass
class Message:
    id: str
    channel_id: str
    author_id: str
    content: str
    timestamp: datetime
    attachments: list[dict] = field(default_factory=list)
    embeds: list[dict] = field(default_factory=list)
    guild_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        ts = data.get("timestamp", "")
        if isinstance(ts, str):
            ts = ts.replace("+00:00", "").replace("Z", "")
            try:
                timestamp = datetime.fromisoformat(ts)
            except ValueError:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        return cls(
            id=data["id"],
            channel_id=data["channel_id"],
            author_id=data["author"]["id"] if "author" in data else "",
            content=data.get("content", ""),
            timestamp=timestamp,
            attachments=data.get("attachments", []),
            embeds=data.get("embeds", []),
            guild_id=data.get("guild_id"),
        )


@dataclass
class SearchFilter:
    author_id: Optional[str] = None
    guild_ids: list[str] = field(default_factory=list)
    channel_ids: list[str] = field(default_factory=list)
    before: Optional[datetime] = None
    after: Optional[datetime] = None
    content: Optional[str] = None
    has_link: Optional[bool] = None
    has_file: Optional[bool] = None
    has_embed: Optional[bool] = None
    min_id: Optional[str] = None
    max_id: Optional[str] = None

    def to_search_params(self) -> dict:
        params = {}
        if self.author_id:
            params["author_id"] = self.author_id
        if self.content:
            params["content"] = self.content
        if self.before:
            from ..utils.snowflake import datetime_to_snowflake
            params["max_id"] = self.max_id or str(datetime_to_snowflake(self.before))
        if self.after:
            from ..utils.snowflake import datetime_to_snowflake
            params["min_id"] = self.min_id or str(datetime_to_snowflake(self.after))
        if self.has_link:
            params["has"] = params.get("has", [])
            if isinstance(params["has"], str):
                params["has"] = [params["has"]]
            params["has"].append("link")
        if self.has_file:
            params["has"] = params.get("has", [])
            if isinstance(params["has"], str):
                params["has"] = [params["has"]]
            params["has"].append("file")
        if self.has_embed:
            params["has"] = params.get("has", [])
            if isinstance(params["has"], str):
                params["has"] = [params["has"]]
            params["has"].append("embed")
        return params


@dataclass
class DeletionJob:
    id: Optional[int] = None
    profile_id: Optional[int] = None
    status: JobStatus = JobStatus.PENDING
    total_messages: int = 0
    deleted_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    filters: Optional[SearchFilter] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def progress(self) -> float:
        if self.total_messages == 0:
            return 0.0
        return (self.deleted_count + self.failed_count + self.skipped_count) / self.total_messages

    @property
    def rate(self) -> float:
        if not self.started_at or self.deleted_count == 0:
            return 0.0
        elapsed = (datetime.now() - self.started_at).total_seconds()
        if elapsed == 0:
            return 0.0
        return self.deleted_count / elapsed


@dataclass
class Profile:
    id: Optional[int] = None
    name: str = ""
    user_id: str = ""
    username: str = ""
    discriminator: str = "0"
    avatar: Optional[str] = None
    is_active: bool = False
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


@dataclass
class ScheduledJob:
    id: Optional[int] = None
    profile_id: Optional[int] = None
    name: str = ""
    cron_expression: str = ""
    enabled: bool = True
    guild_ids: list[str] = field(default_factory=list)
    channel_ids: list[str] = field(default_factory=list)
    filters: Optional[SearchFilter] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class AnalyticsData:
    total_messages: int = 0
    total_servers: int = 0
    total_channels: int = 0
    total_deleted: int = 0
    messages_by_server: dict[str, int] = field(default_factory=dict)
    messages_by_channel: dict[str, int] = field(default_factory=dict)
    messages_by_date: dict[str, int] = field(default_factory=dict)
    messages_by_hour: dict[int, int] = field(default_factory=dict)
    messages_by_day_of_week: dict[int, int] = field(default_factory=dict)
    activity_heatmap: dict[tuple[int, int], int] = field(default_factory=dict)
    estimated_storage_mb: float = 0.0


@dataclass
class AppSettings:
    delete_delay: float = 0.4
    retry_count: int = 5
    confirm_before_delete: bool = True
    scanline_enabled: bool = True
    animation_speed: float = 1.0
    accent_color: str = "#00f0ff"
    minimize_to_tray: bool = True
    db_path: str = ""
    export_path: str = ""
