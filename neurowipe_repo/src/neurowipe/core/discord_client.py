"""Discord HTTP client for all API interactions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import httpx

from ..constants import (
    DISCORD_API_BASE,
    DISCORD_USER_AGENT,
    MAX_RETRIES,
    SEARCH_INDEX_MAX_RETRIES,
    SEARCH_INDEX_RETRY_DELAY,
)
from .exceptions import DeletionError, RateLimitError, SearchError, TokenError
from .models import Channel, Guild, Message, UserInfo
from .rate_limiter import RateLimiter

logger = logging.getLogger("neurowipe.discord_client")


class DiscordClient:
    """Async HTTP client for Discord API."""

    def __init__(self, token: str, rate_limiter: RateLimiter | None = None):
        self.token = token
        self.rate_limiter = rate_limiter or RateLimiter()
        self._client: httpx.AsyncClient | None = None
        self._user_info: UserInfo | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            import base64
            import json as _json

            # Build X-Super-Properties to mimic browser
            super_properties = base64.b64encode(
                _json.dumps({
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": DISCORD_USER_AGENT,
                    "browser_version": "120.0.0.0",
                    "os_version": "10",
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": 250484,
                }).encode()
            ).decode()

            self._client = httpx.AsyncClient(
                base_url=DISCORD_API_BASE,
                headers={
                    "Authorization": self.token,
                    "User-Agent": DISCORD_USER_AGENT,
                    "Content-Type": "application/json",
                    "X-Super-Properties": super_properties,
                    "X-Discord-Locale": "en-US",
                    "X-Discord-Timezone": "America/New_York",
                },
                http2=False,
                timeout=httpx.Timeout(15.0, connect=10.0),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        retries: int = MAX_RETRIES,
    ) -> httpx.Response:
        """Make a rate-limited request to the Discord API."""
        client = await self._get_client()

        for attempt in range(retries):
            await self.rate_limiter.acquire(method, path)

            try:
                logger.debug(f"Request: {method} {path} (attempt {attempt + 1}/{retries})")
                response = await client.request(method, path, params=params, json=json)
                logger.debug(f"Response: {response.status_code} from {method} {path}")
            except httpx.HTTPError as e:
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"HTTP error on {method} {path}: {e}, retry in {wait}s")
                    await asyncio.sleep(wait)
                    continue
                raise

            # Update rate limit info
            self.rate_limiter.update_from_headers(method, path, dict(response.headers))
            self.rate_limiter.check_adaptive_cooldown()

            if response.status_code == 429:
                data = response.json()
                retry_after = data.get("retry_after", 5.0)
                is_global = data.get("global", False)

                if is_global:
                    self.rate_limiter.set_global_limit(retry_after)
                self.rate_limiter.record_rate_limit(retry_after)

                logger.warning(
                    f"Rate limited on {method} {path} "
                    f"({'global' if is_global else 'bucket'}), "
                    f"retry after {retry_after}s (attempt {attempt + 1}/{retries})"
                )

                if attempt < retries - 1:
                    await asyncio.sleep(retry_after)
                    continue
                raise RateLimitError(retry_after)

            if response.status_code == 401:
                raise TokenError("Invalid or expired token")

            if response.status_code == 403:
                logger.warning(f"Forbidden: {method} {path}")
                return response

            return response

        raise SearchError(f"Max retries exceeded for {method} {path}")

    # --- Auth ---

    async def validate_token(self) -> UserInfo:
        """Validate token and return user info."""
        response = await self._request("GET", "/users/@me")
        if response.status_code != 200:
            raise TokenError(f"Token validation failed: {response.status_code}")
        data = response.json()
        self._user_info = UserInfo.from_dict(data)
        logger.info(f"Authenticated as {self._user_info.display_name} ({self._user_info.id})")
        return self._user_info

    @property
    def user_info(self) -> UserInfo | None:
        return self._user_info

    # --- Guilds ---

    async def get_guilds(self) -> list[Guild]:
        """Get all guilds the user is in."""
        guilds = []
        after = "0"
        while True:
            response = await self._request(
                "GET", "/users/@me/guilds", params={"limit": 200, "after": after}
            )
            if response.status_code != 200:
                break
            data = response.json()
            if not data:
                break
            for g in data:
                guilds.append(Guild.from_dict(g))
            if len(data) < 200:
                break
            after = data[-1]["id"]
        logger.info(f"Loaded {len(guilds)} guilds")
        return guilds

    # --- Channels ---

    async def get_guild_channels(self, guild_id: str) -> list[Channel]:
        """Get all channels in a guild."""
        response = await self._request("GET", f"/guilds/{guild_id}/channels")
        if response.status_code != 200:
            return []
        data = response.json()
        channels = []
        for ch in data:
            channel = Channel.from_dict(ch)
            if channel.is_text:
                channels.append(channel)
        return sorted(channels, key=lambda c: c.position)

    async def get_dm_channels(self) -> list[Channel]:
        """Get all DM channels."""
        response = await self._request("GET", "/users/@me/channels")
        if response.status_code != 200:
            return []
        data = response.json()
        channels = []
        for ch in data:
            channel = Channel.from_dict(ch)
            channels.append(channel)
        return channels

    # --- Search ---

    async def search_guild(
        self, guild_id: str, params: dict, offset: int = 0
    ) -> tuple[list[Message], int]:
        """Search messages in a guild. Returns (messages, total_count)."""
        search_params = {**params, "offset": offset}
        for attempt in range(SEARCH_INDEX_MAX_RETRIES):
            response = await self._request(
                "GET", f"/guilds/{guild_id}/messages/search", params=search_params
            )
            if response.status_code == 202:
                logger.info("Search index not ready, retrying...")
                await asyncio.sleep(SEARCH_INDEX_RETRY_DELAY * (2 ** attempt))
                continue
            if response.status_code != 200:
                raise SearchError(f"Guild search failed: {response.status_code}")
            data = response.json()
            total = data.get("total_results", 0)
            messages = []
            for group in data.get("messages", []):
                if group:
                    msg = group[0] if isinstance(group, list) else group
                    messages.append(Message.from_dict(msg))
            return messages, total

        raise SearchError("Search index not ready after max retries")

    async def search_channel(
        self, channel_id: str, params: dict, offset: int = 0
    ) -> tuple[list[Message], int]:
        """Search messages in a specific channel."""
        search_params = {**params, "offset": offset}
        for attempt in range(SEARCH_INDEX_MAX_RETRIES):
            response = await self._request(
                "GET", f"/channels/{channel_id}/messages/search", params=search_params
            )
            if response.status_code == 202:
                logger.info("Search index not ready, retrying...")
                await asyncio.sleep(SEARCH_INDEX_RETRY_DELAY * (2 ** attempt))
                continue
            if response.status_code != 200:
                raise SearchError(f"Channel search failed: {response.status_code}")
            data = response.json()
            total = data.get("total_results", 0)
            messages = []
            for group in data.get("messages", []):
                if group:
                    msg = group[0] if isinstance(group, list) else group
                    messages.append(Message.from_dict(msg))
            return messages, total

        raise SearchError("Search index not ready after max retries")

    # --- Messages ---

    async def get_messages(
        self, channel_id: str, limit: int = 100, before: str | None = None
    ) -> list[Message]:
        """Get messages from a channel."""
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if before:
            params["before"] = before
        response = await self._request("GET", f"/channels/{channel_id}/messages", params=params)
        if response.status_code != 200:
            return []
        data = response.json()
        return [Message.from_dict(m) for m in data]

    async def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a single message. Returns True on success."""
        response = await self._request(
            "DELETE", f"/channels/{channel_id}/messages/{message_id}"
        )
        if response.status_code == 204:
            return True
        if response.status_code == 404:
            logger.debug(f"Message {message_id} already deleted")
            return True
        if response.status_code == 403:
            logger.warning(f"Cannot delete message {message_id}: forbidden")
            return False
        raise DeletionError(
            f"Failed to delete message {message_id}: {response.status_code}"
        )
