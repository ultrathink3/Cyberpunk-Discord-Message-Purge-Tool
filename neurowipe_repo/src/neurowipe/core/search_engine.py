"""Message search engine with pagination and filter application."""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator

from .discord_client import DiscordClient
from .exceptions import CancelledError, SearchError
from .models import Message, SearchFilter

logger = logging.getLogger("neurowipe.search_engine")


class SearchEngine:
    """Handles message search with pagination across guilds and channels."""

    def __init__(self, client: DiscordClient):
        self.client = client
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def reset(self) -> None:
        self._cancelled = False

    async def count_messages(
        self, search_filter: SearchFilter
    ) -> dict[str, int]:
        """Count messages matching filter without fetching all. Returns {context_id: count}."""
        self.reset()
        counts: dict[str, int] = {}
        user_info = self.client.user_info
        if not user_info:
            raise SearchError("Not authenticated")

        params = search_filter.to_search_params()
        params["author_id"] = user_info.id

        if search_filter.guild_ids:
            for guild_id in search_filter.guild_ids:
                if self._cancelled:
                    raise CancelledError("Search cancelled")
                try:
                    _, total = await self.client.search_guild(guild_id, params)
                    counts[guild_id] = total
                except SearchError as e:
                    logger.warning(f"Failed to count in guild {guild_id}: {e}")
                    counts[guild_id] = 0

        if search_filter.channel_ids:
            for channel_id in search_filter.channel_ids:
                if self._cancelled:
                    raise CancelledError("Search cancelled")
                try:
                    _, total = await self.client.search_channel(channel_id, params)
                    counts[channel_id] = total
                except SearchError as e:
                    logger.warning(f"Failed to count in channel {channel_id}: {e}")
                    counts[channel_id] = 0

        return counts

    async def search_messages(
        self, search_filter: SearchFilter
    ) -> AsyncGenerator[list[Message], None]:
        """Search and yield message batches matching filter."""
        self.reset()
        user_info = self.client.user_info
        if not user_info:
            raise SearchError("Not authenticated")

        params = search_filter.to_search_params()
        params["author_id"] = user_info.id

        if search_filter.guild_ids:
            for guild_id in search_filter.guild_ids:
                async for batch in self._search_context(
                    "guild", guild_id, params
                ):
                    yield batch

        if search_filter.channel_ids:
            for channel_id in search_filter.channel_ids:
                async for batch in self._search_context(
                    "channel", channel_id, params
                ):
                    yield batch

    async def _search_context(
        self, context_type: str, context_id: str, params: dict
    ) -> AsyncGenerator[list[Message], None]:
        """Search within a specific guild or channel with pagination."""
        offset = 0
        total = None

        while True:
            if self._cancelled:
                raise CancelledError("Search cancelled")

            try:
                if context_type == "guild":
                    messages, total_count = await self.client.search_guild(
                        context_id, params, offset=offset
                    )
                else:
                    messages, total_count = await self.client.search_channel(
                        context_id, params, offset=offset
                    )
            except SearchError as e:
                logger.error(f"Search error in {context_type} {context_id}: {e}")
                break

            if total is None:
                total = total_count
                logger.info(f"Found {total} messages in {context_type} {context_id}")

            if not messages:
                break

            yield messages

            offset += len(messages)
            if total and offset >= total:
                break

            # Small delay between search pages
            await asyncio.sleep(0.5)

    async def fetch_all_messages(
        self, channel_id: str, author_id: str | None = None
    ) -> AsyncGenerator[list[Message], None]:
        """Fetch all messages from a channel using pagination (non-search fallback)."""
        self.reset()
        before: str | None = None

        while True:
            if self._cancelled:
                raise CancelledError("Fetch cancelled")

            messages = await self.client.get_messages(channel_id, limit=100, before=before)
            if not messages:
                break

            if author_id:
                messages = [m for m in messages if m.author_id == author_id]

            if messages:
                yield messages

            before = messages[-1].id if messages else None
            await asyncio.sleep(0.3)
