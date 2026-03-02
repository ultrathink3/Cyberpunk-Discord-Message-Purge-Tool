"""Input validation utilities."""

import re


def validate_token(token: str) -> bool:
    """Basic validation of a Discord user token format."""
    token = token.strip()
    if not token:
        return False
    # User tokens are base64-encoded and typically have 2-3 dot-separated parts
    parts = token.split(".")
    if len(parts) < 2:
        return False
    if len(token) < 40:
        return False
    return True


def validate_snowflake(snowflake: str) -> bool:
    """Validate a Discord snowflake ID."""
    if not snowflake:
        return False
    try:
        val = int(snowflake)
        return val > 0
    except ValueError:
        return False


def validate_cron(expression: str) -> bool:
    """Basic validation of a cron expression."""
    parts = expression.strip().split()
    if len(parts) not in (5, 6):
        return False
    return True


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    if not name:
        name = "unnamed"
    return name[:200]


def validate_delay(delay: float) -> float:
    """Clamp delay to valid range."""
    return max(0.2, min(2.0, delay))


def validate_export_path(path: str) -> bool:
    """Check if export path is valid."""
    if not path:
        return False
    import os
    return os.path.isdir(path) or os.path.isdir(os.path.dirname(path))
