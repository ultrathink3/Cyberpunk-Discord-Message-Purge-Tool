"""Application-wide constants."""

APP_NAME = "NEUROWIPE"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Erase Your Digital Trace"
APP_DESCRIPTION = "Cyberpunk Discord Message Purge Tool"

# Discord API
DISCORD_API_BASE = "https://discord.com/api/v9"
DISCORD_CDN_BASE = "https://cdn.discordapp.com"
DISCORD_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Rate limiting
DEFAULT_DELETE_DELAY = 0.4  # seconds between deletes
MIN_DELETE_DELAY = 0.2
MAX_DELETE_DELAY = 2.0
JITTER_MIN = 0.05  # 50ms
JITTER_MAX = 0.15  # 150ms
MAX_RETRIES = 5
GLOBAL_RATE_LIMIT = 50  # requests per second
RATE_LIMIT_ESCALATION_THRESHOLD = 3  # hits in window before backing off
RATE_LIMIT_ESCALATION_WINDOW = 60  # seconds
RATE_LIMIT_COOLDOWN = 120  # seconds of clean operation before reducing delay

# Search
SEARCH_PAGE_SIZE = 25  # Discord's default
SEARCH_INDEX_RETRY_DELAY = 2.0  # seconds for 202 retry
SEARCH_INDEX_MAX_RETRIES = 10

# Database
DB_FILENAME = "neurowipe.db"
DB_VERSION = 1

# Token vault
VAULT_SERVICE_NAME = "neurowipe"
FERNET_KEY_FILE = ".neurowipe_key"

# Window
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 700
WINDOW_DEFAULT_WIDTH = 1280
WINDOW_DEFAULT_HEIGHT = 800
SIDEBAR_WIDTH = 200
SIDEBAR_COLLAPSED_WIDTH = 60
TITLE_BAR_HEIGHT = 40

# Export
EXPORT_FORMATS = ["JSON", "CSV", "TXT"]
EXPORT_CHUNK_SIZE = 100  # messages per batch

# Scheduler
SCHEDULER_CHECK_INTERVAL = 30  # seconds

# Logging
LOG_MAX_LINES = 5000
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
