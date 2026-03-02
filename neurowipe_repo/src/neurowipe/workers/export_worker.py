"""Worker for message export operations."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal

from ..core.exceptions import CancelledError
from ..core.export_engine import ExportEngine
from ..core.models import ExportFormat, SearchFilter
from .async_bridge import AsyncBridge
from .base_worker import BaseWorker


class ExportWorker(BaseWorker):
    """Bridges ExportEngine async operations to Qt signals."""

    export_complete = Signal(str)  # export path

    def __init__(self, bridge: AsyncBridge, export_engine: ExportEngine, parent=None):
        super().__init__(parent)
        self._bridge = bridge
        self._engine = export_engine

        self._engine.set_callbacks(
            on_progress=self._on_progress,
            on_log=self._on_log,
        )

    def start_export(
        self,
        search_filter: SearchFilter,
        output_dir: str,
        format: ExportFormat,
        organize_by_channel: bool = True,
    ) -> None:
        """Start message export."""
        self.reset()
        self._engine.reset()
        self.started.emit()

        async def _do_export():
            try:
                result_path = await self._engine.export(
                    search_filter,
                    Path(output_dir),
                    format,
                    organize_by_channel,
                )
                self.export_complete.emit(str(result_path))
            except CancelledError:
                self._emit_log("WARNING", "Export cancelled")
            except Exception as e:
                self.error.emit(str(e))
                self._emit_log("ERROR", f"Export failed: {e}")
            finally:
                self.finished.emit()

        self._bridge.submit(_do_export())

    def cancel(self) -> None:
        super().cancel()
        self._engine.cancel()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.emit(current, total)

    def _on_log(self, level: str, message: str) -> None:
        self._emit_log(level, message)
