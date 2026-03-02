"""Platform-specific utilities."""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def resource_path(relative_path: str) -> Path:
    """Get absolute path to a resource, works for dev and PyInstaller."""
    if is_frozen():
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent.parent / "resources"
    return base_path / relative_path


def get_data_dir() -> Path:
    """Get the application data directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    data_dir = base / "neurowipe"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """Get the application config directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = base / "neurowipe"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_log_dir() -> Path:
    """Get the log directory."""
    log_dir = get_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_default_export_dir() -> Path:
    """Get default export directory."""
    export_dir = Path.home() / "Documents" / "NEUROWIPE_Exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir
