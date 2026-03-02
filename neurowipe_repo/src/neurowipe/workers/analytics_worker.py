"""Worker for analytics computation."""

from __future__ import annotations

from PySide6.QtCore import Signal

from ..core.analytics_engine import AnalyticsEngine
from ..core.exceptions import CancelledError
from ..core.models import AnalyticsData, SearchFilter
from .async_bridge import AsyncBridge
from .base_worker import BaseWorker


class AnalyticsWorker(BaseWorker):
    """Bridges AnalyticsEngine async operations to Qt signals."""

    analytics_ready = Signal(object)  # AnalyticsData

    def __init__(self, bridge: AsyncBridge, analytics_engine: AnalyticsEngine, parent=None):
        super().__init__(parent)
        self._bridge = bridge
        self._engine = analytics_engine

        self._engine.set_callbacks(on_progress=self._on_progress)

    def compute(self, search_filter: SearchFilter) -> None:
        """Start analytics computation."""
        self.reset()
        self._engine.reset()
        self.started.emit()
        self._emit_log("INFO", "Computing analytics...")

        async def _do_compute():
            try:
                data = await self._engine.compute(search_filter)
                self.analytics_ready.emit(data)
                self._emit_log("INFO", "Analytics computation complete")
            except CancelledError:
                self._emit_log("WARNING", "Analytics cancelled")
            except Exception as e:
                self.error.emit(str(e))
                self._emit_log("ERROR", f"Analytics failed: {e}")
            finally:
                self.finished.emit()

        self._bridge.submit(_do_compute())

    def cancel(self) -> None:
        super().cancel()
        self._engine.cancel()

    def _on_progress(self, count: int) -> None:
        self.progress.emit(count, 0)
