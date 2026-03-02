"""Analytics computation engine for message statistics."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

from .discord_client import DiscordClient
from .exceptions import CancelledError
from .models import AnalyticsData, Message, SearchFilter
from .search_engine import SearchEngine

logger = logging.getLogger("neurowipe.analytics_engine")


class AnalyticsEngine:
    """Computes analytics and statistics from Discord messages."""

    def __init__(self, client: DiscordClient, search_engine: SearchEngine):
        self.client = client
        self.search_engine = search_engine
        self._cancelled = False
        self._on_progress: Callable[[int], None] | None = None

    def set_callbacks(
        self,
        on_progress: Callable[[int], None] | None = None,
    ) -> None:
        self._on_progress = on_progress

    def cancel(self) -> None:
        self._cancelled = True
        self.search_engine.cancel()

    def reset(self) -> None:
        self._cancelled = False
        self.search_engine.reset()

    async def compute(self, search_filter: SearchFilter) -> AnalyticsData:
        """Compute analytics for messages matching filter."""
        self.reset()
        data = AnalyticsData()

        messages_by_server: dict[str, int] = defaultdict(int)
        messages_by_channel: dict[str, int] = defaultdict(int)
        messages_by_date: dict[str, int] = defaultdict(int)
        messages_by_hour: dict[int, int] = defaultdict(int)
        messages_by_dow: dict[int, int] = defaultdict(int)
        heatmap: dict[tuple[int, int], int] = defaultdict(int)
        servers_seen: set[str] = set()
        channels_seen: set[str] = set()
        total_content_length = 0
        count = 0

        try:
            async for batch in self.search_engine.search_messages(search_filter):
                if self._cancelled:
                    raise CancelledError("Analytics cancelled")

                for msg in batch:
                    count += 1
                    guild_id = msg.guild_id or "DMs"
                    messages_by_server[guild_id] += 1
                    messages_by_channel[msg.channel_id] += 1
                    servers_seen.add(guild_id)
                    channels_seen.add(msg.channel_id)

                    date_key = msg.timestamp.strftime("%Y-%m-%d")
                    messages_by_date[date_key] += 1

                    hour = msg.timestamp.hour
                    dow = msg.timestamp.weekday()
                    messages_by_hour[hour] += 1
                    messages_by_dow[dow] += 1
                    heatmap[(dow, hour)] += 1

                    total_content_length += len(msg.content)
                    for att in msg.attachments:
                        total_content_length += att.get("size", 0)

                if self._on_progress:
                    self._on_progress(count)

        except CancelledError:
            logger.info("Analytics computation cancelled")

        data.total_messages = count
        data.total_servers = len(servers_seen)
        data.total_channels = len(channels_seen)
        data.messages_by_server = dict(messages_by_server)
        data.messages_by_channel = dict(messages_by_channel)
        data.messages_by_date = dict(messages_by_date)
        data.messages_by_hour = dict(messages_by_hour)
        data.messages_by_day_of_week = dict(messages_by_dow)
        data.activity_heatmap = dict(heatmap)
        data.estimated_storage_mb = total_content_length / (1024 * 1024)

        logger.info(
            f"Analytics complete: {count} messages, "
            f"{data.total_servers} servers, {data.total_channels} channels"
        )
        return data
