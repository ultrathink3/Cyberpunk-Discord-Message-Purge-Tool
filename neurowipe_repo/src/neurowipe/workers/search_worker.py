"""Worker for message search operations."""

from __future__ import annotations

from PySide6.QtCore import Signal

from ..core.exceptions import CancelledError
from ..core.models import SearchFilter
from ..core.search_engine import SearchEngine
from .async_bridge import AsyncBridge
from .base_worker import BaseWorker


class SearchWorker(BaseWorker):
    """Bridges SearchEngine async operations to Qt signals."""

    count_result = Signal(int)  # total message count
    scan_complete = Signal(dict)  # {context_id: count}

    def __init__(self, bridge: AsyncBridge, search_engine: SearchEngine, parent=None):
        super().__init__(parent)
        self._bridge = bridge
        self._search_engine = search_engine

    def scan(self, search_filter: SearchFilter) -> None:
        """Start a scan operation to count messages."""
        self.reset()
        self._search_engine.reset()
        self.started.emit()
        self._emit_log("INFO", "Scanning for messages...")

        async def _do_scan():
            try:
                counts = await self._search_engine.count_messages(search_filter)
                total = sum(counts.values())
                self.count_result.emit(total)
                self.scan_complete.emit(counts)
                self._emit_log("INFO", f"Scan complete: {total} messages found")
            except CancelledError:
                self._emit_log("WARNING", "Scan cancelled")
            except Exception as e:
                self.error.emit(str(e))
                self._emit_log("ERROR", f"Scan failed: {e}")
            finally:
                self.finished.emit()

        self._bridge.submit(_do_scan())

    def cancel(self) -> None:
        super().cancel()
        self._search_engine.cancel()
