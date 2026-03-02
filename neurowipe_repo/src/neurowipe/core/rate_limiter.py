"""Bucket-based rate limiter for Discord API with adaptive throttling."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

from ..constants import (
    DEFAULT_DELETE_DELAY,
    GLOBAL_RATE_LIMIT,
    JITTER_MAX,
    JITTER_MIN,
    RATE_LIMIT_COOLDOWN,
    RATE_LIMIT_ESCALATION_THRESHOLD,
    RATE_LIMIT_ESCALATION_WINDOW,
)

logger = logging.getLogger("neurowipe.rate_limiter")


@dataclass
class RateBucket:
    """Tracks rate limit state for a specific API route bucket."""

    remaining: int = 1
    limit: int = 1
    reset_at: float = 0.0
    bucket_id: str = ""


@dataclass
class RateLimiter:
    """Manages Discord API rate limiting with bucket tracking and adaptive throttling."""

    delete_delay: float = DEFAULT_DELETE_DELAY
    _buckets: dict[str, RateBucket] = field(default_factory=dict)
    _route_to_bucket: dict[str, str] = field(default_factory=dict)
    _global_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _global_reset_at: float = 0.0
    _request_timestamps: list[float] = field(default_factory=list)
    _rate_limit_hits: list[float] = field(default_factory=list)
    _last_clean_window_start: float = 0.0
    _adaptive_multiplier: float = 1.0
    _locks: dict[str, asyncio.Lock] = field(default_factory=lambda: defaultdict(asyncio.Lock))

    def _get_route_key(self, method: str, path: str) -> str:
        """Generate a rate limit route key."""
        parts = path.strip("/").split("/")
        normalized = []
        skip_next = False
        for i, part in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
            if part in ("channels", "guilds", "webhooks") and i + 1 < len(parts):
                normalized.append(part)
                normalized.append(parts[i + 1])
                skip_next = True
            else:
                normalized.append(part)
        return f"{method}:{'/'.join(normalized)}"

    async def acquire(self, method: str, path: str) -> None:
        """Wait until it's safe to make a request."""
        route_key = self._get_route_key(method, path)
        lock = self._locks[route_key]

        async with lock:
            # Global rate limit check
            now = time.monotonic()
            if self._global_reset_at > now:
                wait = self._global_reset_at - now
                logger.warning(f"Global rate limit, waiting {wait:.2f}s")
                await asyncio.sleep(wait)

            # Sliding window global limit
            self._request_timestamps = [
                t for t in self._request_timestamps if t > time.monotonic() - 1.0
            ]
            if len(self._request_timestamps) >= GLOBAL_RATE_LIMIT:
                wait = 1.0 - (time.monotonic() - self._request_timestamps[0])
                if wait > 0:
                    await asyncio.sleep(wait)

            # Bucket-specific check
            bucket_id = self._route_to_bucket.get(route_key)
            if bucket_id and bucket_id in self._buckets:
                bucket = self._buckets[bucket_id]
                if bucket.remaining <= 0 and bucket.reset_at > time.monotonic():
                    wait = bucket.reset_at - time.monotonic()
                    logger.debug(f"Bucket {bucket_id} exhausted, waiting {wait:.2f}s")
                    await asyncio.sleep(wait)

            self._request_timestamps.append(time.monotonic())

    async def wait_delete_delay(self) -> None:
        """Wait the configured delay between delete operations with jitter."""
        jitter = random.uniform(JITTER_MIN, JITTER_MAX)
        delay = self.delete_delay * self._adaptive_multiplier + jitter
        await asyncio.sleep(delay)

    def update_from_headers(self, method: str, path: str, headers: dict) -> None:
        """Update rate limit state from response headers."""
        route_key = self._get_route_key(method, path)

        bucket_id = headers.get("x-ratelimit-bucket", "")
        if bucket_id:
            self._route_to_bucket[route_key] = bucket_id

            remaining = int(headers.get("x-ratelimit-remaining", 1))
            limit = int(headers.get("x-ratelimit-limit", 1))
            reset_after = float(headers.get("x-ratelimit-reset-after", 0))

            self._buckets[bucket_id] = RateBucket(
                remaining=remaining,
                limit=limit,
                reset_at=time.monotonic() + reset_after,
                bucket_id=bucket_id,
            )

    def record_rate_limit(self, retry_after: float) -> None:
        """Record a rate limit hit for adaptive throttling."""
        now = time.monotonic()
        self._rate_limit_hits.append(now)
        self._rate_limit_hits = [
            t for t in self._rate_limit_hits if t > now - RATE_LIMIT_ESCALATION_WINDOW
        ]
        if len(self._rate_limit_hits) >= RATE_LIMIT_ESCALATION_THRESHOLD:
            self._adaptive_multiplier = min(self._adaptive_multiplier * 1.5, 5.0)
            logger.warning(
                f"Adaptive throttle escalated to {self._adaptive_multiplier:.1f}x "
                f"({len(self._rate_limit_hits)} hits in {RATE_LIMIT_ESCALATION_WINDOW}s)"
            )
            self._last_clean_window_start = 0.0

    def set_global_limit(self, retry_after: float) -> None:
        """Set a global rate limit pause."""
        self._global_reset_at = time.monotonic() + retry_after
        logger.warning(f"Global rate limit set for {retry_after:.2f}s")

    def check_adaptive_cooldown(self) -> None:
        """Reduce adaptive multiplier after clean period."""
        now = time.monotonic()
        recent_hits = [
            t for t in self._rate_limit_hits if t > now - RATE_LIMIT_COOLDOWN
        ]
        if not recent_hits and self._adaptive_multiplier > 1.0:
            if self._last_clean_window_start == 0.0:
                self._last_clean_window_start = now
            elif now - self._last_clean_window_start > RATE_LIMIT_COOLDOWN:
                self._adaptive_multiplier = max(self._adaptive_multiplier * 0.75, 1.0)
                self._last_clean_window_start = now
                logger.info(
                    f"Adaptive throttle reduced to {self._adaptive_multiplier:.1f}x"
                )
        else:
            self._last_clean_window_start = 0.0

    @property
    def effective_delay(self) -> float:
        """Current effective delay between operations."""
        return self.delete_delay * self._adaptive_multiplier
