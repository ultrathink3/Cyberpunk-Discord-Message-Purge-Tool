"""AsyncBridge — runs an asyncio event loop in a dedicated QThread."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import Future
from typing import Any, Callable, Coroutine

from PySide6.QtCore import QThread, Signal, QMetaObject, Qt, Slot, QObject

logger = logging.getLogger("neurowipe.async_bridge")


class _CallbackInvoker(QObject):
    """Helper to invoke callbacks on the main thread via signal."""
    invoke_signal = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoke_signal.connect(self._run, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _run(self, func):
        try:
            func()
        except Exception as e:
            logger.exception(f"Callback invoker error: {e}")


class AsyncBridge(QThread):
    """Runs an asyncio event loop in a QThread for async core operations.

    Submit coroutines from the main Qt thread via submit().
    Results are returned via Qt Signals on the worker objects.
    """

    started_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ready = False
        self._invoker = _CallbackInvoker()

    def call_on_main_thread(self, func: Callable) -> None:
        """Safely invoke a callable on the main Qt thread from any thread."""
        self._invoker.invoke_signal.emit(func)

    @property
    def loop(self) -> asyncio.AbstractEventLoop | None:
        return self._loop

    @property
    def is_ready(self) -> bool:
        return self._ready and self._loop is not None and self._loop.is_running()

    def run(self) -> None:
        """QThread entry point — create and run the asyncio event loop."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ready = True
            self.started_signal.emit()
            logger.info("AsyncBridge event loop started")
            self._loop.run_forever()
        except Exception as e:
            logger.exception("AsyncBridge event loop error")
            self.error_signal.emit(str(e))
        finally:
            if self._loop and not self._loop.is_closed():
                # Run pending cleanup
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
                self._loop.close()
            self._ready = False
            logger.info("AsyncBridge event loop stopped")

    def submit(self, coro: Coroutine) -> Future:
        """Submit a coroutine to the async event loop from any thread.

        Returns a concurrent.futures.Future that can be used to get the result.
        """
        if not self.is_ready:
            future: Future = Future()
            future.set_exception(RuntimeError("AsyncBridge not ready"))
            return future
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def stop(self) -> None:
        """Stop the event loop and wait for thread to finish."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.wait(5000)
        logger.info("AsyncBridge stopped")
