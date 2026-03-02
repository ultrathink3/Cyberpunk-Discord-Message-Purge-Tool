"""Neon cyberpunk color palette."""


class Colors:
    """Central color definitions for the cyberpunk theme."""

    # Backgrounds (dark to light)
    BG_DARKEST = "#0a0a0f"
    BG_MAIN = "#0d1117"
    BG_CARD = "#161b22"
    BG_HOVER = "#1c2333"
    BG_INPUT = "#0f1318"
    BG_SELECTED = "#1a2332"

    # Borders
    BORDER = "#21262d"
    BORDER_FOCUS = "#30363d"
    BORDER_GLOW = "#00f0ff"

    # Primary accents
    CYAN = "#00f0ff"
    MAGENTA = "#ff00aa"
    ELECTRIC_PURPLE = "#bf00ff"

    # Status
    SUCCESS = "#00ff88"
    ERROR = "#ff2255"
    WARNING = "#ffcc00"

    # Text
    TEXT_PRIMARY = "#e6edf3"
    TEXT_SECONDARY = "#8b949e"
    TEXT_MUTED = "#484f58"
    TEXT_BRIGHT = "#ffffff"

    # Gradients (for progress bars, etc.)
    GRADIENT_START = CYAN
    GRADIENT_MID = ELECTRIC_PURPLE
    GRADIENT_END = MAGENTA

    # Scrollbar
    SCROLLBAR_BG = "#0d1117"
    SCROLLBAR_HANDLE = "#21262d"
    SCROLLBAR_HANDLE_HOVER = "#30363d"

    # Sidebar
    SIDEBAR_BG = "#010409"
    SIDEBAR_ACTIVE = "#0d1117"
    SIDEBAR_HOVER = "#161b22"

    # Title bar
    TITLEBAR_BG = "#010409"

    # Button states
    BUTTON_BG = "#21262d"
    BUTTON_HOVER = "#30363d"
    BUTTON_PRESSED = "#0d1117"
    BUTTON_DISABLED = "#161b22"

    @classmethod
    def with_alpha(cls, hex_color: str, alpha: float) -> str:
        """Return rgba() string from hex color and alpha (0.0–1.0)."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    @classmethod
    def to_rgb_tuple(cls, hex_color: str) -> tuple[int, int, int]:
        """Convert hex to (r, g, b) tuple."""
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
