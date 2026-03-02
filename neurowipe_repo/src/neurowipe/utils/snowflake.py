"""Discord snowflake ID <-> datetime conversion utilities."""

from datetime import datetime, timezone

DISCORD_EPOCH = 1420070400000  # 2015-01-01T00:00:00.000Z in ms


def snowflake_to_datetime(snowflake: str | int) -> datetime:
    """Convert a Discord snowflake ID to a datetime."""
    snowflake_int = int(snowflake)
    timestamp_ms = (snowflake_int >> 22) + DISCORD_EPOCH
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def datetime_to_snowflake(dt: datetime) -> int:
    """Convert a datetime to a Discord snowflake ID."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    timestamp_ms = int(dt.timestamp() * 1000)
    return (timestamp_ms - DISCORD_EPOCH) << 22


def snowflake_to_timestamp(snowflake: str | int) -> float:
    """Convert a Discord snowflake to a Unix timestamp."""
    snowflake_int = int(snowflake)
    return ((snowflake_int >> 22) + DISCORD_EPOCH) / 1000
