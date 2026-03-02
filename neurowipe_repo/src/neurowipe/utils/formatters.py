"""Formatting utilities."""

from datetime import datetime, timedelta


def format_count(count: int) -> str:
    """Format a number with K/M suffixes."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    td = timedelta(seconds=int(seconds))
    parts = []
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if td.days > 0:
        parts.append(f"{td.days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0:
        parts.append(f"{secs}s")
    return " ".join(parts) or "0s"


def format_rate(rate: float) -> str:
    """Format deletion rate."""
    return f"{rate:.1f} msg/s"


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time (e.g., '2 hours ago')."""
    now = datetime.now()
    diff = now - dt
    if diff.days > 365:
        years = diff.days // 365
        return f"{years}y ago"
    if diff.days > 30:
        months = diff.days // 30
        return f"{months}mo ago"
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes}m ago"
    return "just now"


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
