"""Application bootstrap — wires together all components and starts the GUI."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QTimer  # still used by some Qt internals
from PySide6.QtWidgets import QApplication

from .constants import APP_NAME
from .core.analytics_engine import AnalyticsEngine
from .core.database import Database
from .core.deletion_engine import DeletionEngine
from .core.discord_client import DiscordClient
from .core.export_engine import ExportEngine
from .core.models import (
    AppSettings,
    DeletionJob,
    ExportFormat,
    Profile,
    ScheduledJob,
    SearchFilter,
)
from .core.profile_manager import ProfileManager
from .core.rate_limiter import RateLimiter
from .core.scheduler import SchedulerManager
from .core.search_engine import SearchEngine
from .core.token_vault import TokenVault
from .theme.cyberpunk_theme import CyberpunkTheme
from .ui.charts.chart_theme import apply_chart_theme
from .ui.dialogs.confirm_delete_dialog import ConfirmDeleteDialog
from .ui.dialogs.error_dialog import ErrorDialog
from .ui.dialogs.profile_editor_dialog import ProfileEditorDialog
from .ui.dialogs.schedule_editor_dialog import ScheduleEditorDialog
from .ui.main_window import MainWindow
from .utils.logging_config import get_signal_handler, setup_logging
from .utils.platform_utils import get_data_dir, get_log_dir
from .workers.analytics_worker import AnalyticsWorker
from .workers.async_bridge import AsyncBridge
from .workers.deletion_worker import DeletionWorker
from .workers.export_worker import ExportWorker
from .workers.scheduler_worker import SchedulerWorker
from .workers.search_worker import SearchWorker

logger = logging.getLogger("neurowipe.app")


class NeurowipeApp:
    """Main application controller — orchestrates all components."""

    def __init__(self):
        self._qt_app: QApplication | None = None
        self._window: MainWindow | None = None
        self._theme: CyberpunkTheme | None = None
        self._bridge: AsyncBridge | None = None

        # Core
        self._rate_limiter = RateLimiter()
        self._database = Database()
        self._token_vault = TokenVault()
        self._profile_manager: ProfileManager | None = None
        self._scheduler: SchedulerManager | None = None

        # Current session
        self._client: DiscordClient | None = None
        self._search_engine: SearchEngine | None = None
        self._deletion_engine: DeletionEngine | None = None
        self._export_engine: ExportEngine | None = None
        self._analytics_engine: AnalyticsEngine | None = None

        # Workers
        self._search_worker: SearchWorker | None = None
        self._deletion_worker: DeletionWorker | None = None
        self._export_worker: ExportWorker | None = None
        self._analytics_worker: AnalyticsWorker | None = None
        self._scheduler_worker: SchedulerWorker | None = None

        self._settings = AppSettings()

    def run(self) -> int:
        """Start the application."""
        # Global exception hook to prevent silent crashes
        def _exception_hook(exc_type, exc_value, exc_tb):
            import traceback
            logger.critical(
                "Unhandled exception:\n"
                + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            )
            sys.__excepthook__(exc_type, exc_value, exc_tb)

        sys.excepthook = _exception_hook

        self._qt_app = QApplication(sys.argv)
        self._qt_app.setApplicationName(APP_NAME)

        # Setup logging
        setup_logging(get_log_dir())

        # Apply theme
        self._theme = CyberpunkTheme(self._qt_app)
        self._theme.apply()
        apply_chart_theme()

        # Start async bridge
        self._bridge = AsyncBridge()
        self._bridge.started_signal.connect(self._on_bridge_ready)
        self._bridge.error_signal.connect(self._on_bridge_error)
        self._bridge.start()

        # Create main window
        self._window = MainWindow()
        self._connect_signals()
        self._window.show()

        # Start login animations
        self._window.login_view.start_animations()

        # Connect log handler to log view
        signal_handler = get_signal_handler()
        signal_handler.log_message.connect(self._on_global_log)

        return self._qt_app.exec()

    def _on_bridge_ready(self) -> None:
        """Called when the async bridge event loop is ready."""
        logger.info("Async bridge ready, initializing database...")
        future = self._bridge.submit(self._async_init())
        # No need to wait — results come via signals

    async def _async_init(self) -> None:
        """Initialize async components (runs in the async bridge)."""
        try:
            await self._database.connect()
            self._profile_manager = ProfileManager(self._database, self._token_vault)
            self._scheduler = SchedulerManager(self._database)

            # Load settings
            self._settings = await self._database.get_all_settings()
            self._rate_limiter.delete_delay = self._settings.delete_delay

            # Load profiles
            profiles = await self._profile_manager.load_profiles()

            # Update UI from main thread via signal
            self._bridge.call_on_main_thread(lambda _p=profiles: self._apply_loaded_data(_p))
        except Exception as e:
            logger.exception("Failed to initialize application")
            err_msg = str(e)
            self._bridge.call_on_main_thread(
                lambda _msg=err_msg: self._on_bridge_error(_msg)
            )

    def _apply_loaded_data(self, profiles: list[Profile]) -> None:
        """Apply loaded data to UI (called on main thread)."""
        if self._window:
            self._window.login_view.set_profiles(profiles)
            self._window.settings_view.set_profiles(profiles)
            self._window.settings_view.set_settings(self._settings)

            if self._settings.scanline_enabled:
                self._window.scanline_overlay.start()
            else:
                self._window.set_scanline_enabled(False)

            self._window.set_minimize_to_tray(self._settings.minimize_to_tray)

            # Apply theme settings
            if self._theme:
                self._theme.accent_color = self._settings.accent_color
                self._theme.scanline_enabled = self._settings.scanline_enabled

        logger.info("Application initialized")

    def _on_bridge_error(self, error: str) -> None:
        logger.error(f"Async bridge error: {error}")

    # --- Signal connections ---

    def _connect_signals(self) -> None:
        """Wire up all UI signals to handlers."""
        w = self._window

        # Login
        w.login_view.connect_requested.connect(self._on_connect_token)
        w.login_view.profile_connect_requested.connect(self._on_connect_profile)
        w.login_view.new_profile_requested.connect(self._on_new_profile)
        w.login_view.edit_profile_requested.connect(self._on_edit_profile)
        w.login_view.delete_profile_requested.connect(self._on_delete_profile)

        # Purge
        w.purge_view.scan_requested.connect(self._on_scan)
        w.purge_view.purge_requested.connect(self._on_purge)
        w.purge_view.pause_requested.connect(self._on_pause)
        w.purge_view.resume_requested.connect(self._on_resume)
        w.purge_view.cancel_requested.connect(self._on_cancel)

        # Dashboard
        w.dashboard_view.compute_requested.connect(self._on_compute_analytics)

        # Export
        w.export_view.export_requested.connect(self._on_export)

        # Scheduler
        w.scheduler_view.new_job_requested.connect(self._on_new_schedule)
        w.scheduler_view.edit_job_requested.connect(self._on_edit_schedule)
        w.scheduler_view.delete_job_requested.connect(self._on_delete_schedule)
        w.scheduler_view.toggle_job_requested.connect(self._on_toggle_schedule)
        w.scheduler_view.run_now_requested.connect(self._on_run_schedule_now)

        # Settings
        w.settings_view.settings_changed.connect(self._on_settings_changed)
        w.settings_view.new_profile_requested.connect(self._on_new_profile)
        w.settings_view.edit_profile_requested.connect(self._on_edit_profile)
        w.settings_view.delete_profile_requested.connect(self._on_delete_profile)
        w.settings_view.switch_profile_requested.connect(self._on_connect_profile)
        w.settings_view.accent_color_changed.connect(self._on_accent_color_changed)

    # --- Auth handlers ---

    def _on_connect_token(self, token: str) -> None:
        self._window.login_view.set_connecting(True)
        self._window.login_view.set_status("Connecting...")

        async def _do_connect():
            try:
                logger.info("Validating token...")
                client = await self._profile_manager.connect_with_token(
                    token, self._rate_limiter
                )
                self._client = client
                logger.info("Token validated, switching to main thread...")
                # Init engines on main thread (Qt objects must be created there)
                self._bridge.call_on_main_thread(self._init_engines_and_connect)
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Connection failed: {err_msg}")
                self._bridge.call_on_main_thread(
                    lambda _msg=err_msg: self._on_connect_error(_msg)
                )

        self._bridge.submit(_do_connect())

    def _on_connect_profile(self, profile_id: int) -> None:
        self._window.login_view.set_connecting(True)
        self._window.login_view.set_status("Connecting...")

        async def _do_connect():
            try:
                logger.info(f"Connecting profile {profile_id}...")
                client = await self._profile_manager.connect(
                    profile_id, self._rate_limiter
                )
                self._client = client
                logger.info("Profile connected, switching to main thread...")
                self._bridge.call_on_main_thread(self._init_engines_and_connect)
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Profile connection failed: {err_msg}")
                self._bridge.call_on_main_thread(
                    lambda _msg=err_msg: self._on_connect_error(_msg)
                )

        self._bridge.submit(_do_connect())

    def _init_engines_and_connect(self) -> None:
        """Initialize engines + workers on main thread, then finish connection."""
        self._init_engines()
        self._on_connected()

    def _on_connected(self) -> None:
        """Called after successful connection."""
        self._window.login_view.set_connecting(False)
        user = self._client.user_info
        if user:
            self._window.status_bar_widget.set_connected(user.display_name)
            self._window.login_view.set_status(
                f"Connected as {user.display_name}"
            )

        # Load guilds and channels
        self._load_channel_tree()

        # Switch to purge view
        self._window.show_purge()

        # Start scheduler
        if self._scheduler_worker:
            self._scheduler_worker.start_scheduler()
            self._scheduler_worker.load_jobs()

    def _on_connect_error(self, error: str) -> None:
        self._window.login_view.set_connecting(False)
        self._window.login_view.set_status(f"Error: {error}", error=True)
        self._window.status_bar_widget.set_error(error)

    def _init_engines(self) -> None:
        """Initialize all engines with the current client."""
        self._search_engine = SearchEngine(self._client)
        self._deletion_engine = DeletionEngine(
            self._client, self._rate_limiter, self._search_engine
        )
        self._export_engine = ExportEngine(self._client, self._search_engine)
        self._analytics_engine = AnalyticsEngine(self._client, self._search_engine)

        # Workers
        self._search_worker = SearchWorker(self._bridge, self._search_engine)
        self._search_worker.count_result.connect(self._on_scan_result)
        self._search_worker.error.connect(
            lambda e: self._window.purge_view.log_view.append_log("ERROR", e)
        )
        self._search_worker.log_message.connect(
            self._window.purge_view.log_view.append_log
        )

        self._deletion_worker = DeletionWorker(self._bridge, self._deletion_engine)
        self._deletion_worker.job_progress.connect(self._on_deletion_progress)
        self._deletion_worker.job_complete.connect(self._on_deletion_complete)
        self._deletion_worker.log_message.connect(
            self._window.purge_view.log_view.append_log
        )
        self._deletion_worker.error.connect(
            lambda e: self._window.purge_view.log_view.append_log("ERROR", e)
        )

        self._export_worker = ExportWorker(self._bridge, self._export_engine)
        self._export_worker.progress.connect(self._window.export_view.set_progress)
        self._export_worker.export_complete.connect(self._on_export_complete)
        self._export_worker.error.connect(
            lambda e: ErrorDialog.show_error("Export Error", e, parent=self._window)
        )

        self._analytics_worker = AnalyticsWorker(self._bridge, self._analytics_engine)
        self._analytics_worker.analytics_ready.connect(
            self._window.dashboard_view.update_data
        )
        self._analytics_worker.error.connect(
            lambda e: ErrorDialog.show_error("Analytics Error", e, parent=self._window)
        )

        self._scheduler_worker = SchedulerWorker(self._bridge, self._scheduler)
        self._scheduler_worker.jobs_loaded.connect(
            self._window.scheduler_view.set_jobs
        )

    def _load_channel_tree(self) -> None:
        """Load guilds and channels into the channel trees."""
        async def _do_load():
            try:
                guilds = await self._client.get_guilds()
                dm_channels = await self._client.get_dm_channels()

                # Load channels for each guild
                guild_channels = {}
                for guild in guilds:
                    channels = await self._client.get_guild_channels(guild.id)
                    guild_channels[guild.id] = (guild, channels)

                self._bridge.call_on_main_thread(
                    lambda _gc=guild_channels, _dm=dm_channels: self._populate_trees(_gc, _dm)
                )
            except Exception as e:
                logger.error(f"Failed to load channel tree: {e}")

        self._bridge.submit(_do_load())

    def _populate_trees(self, guild_channels, dm_channels) -> None:
        """Populate channel trees in all views."""
        for tree in (
            self._window.purge_view.channel_tree,
            self._window.export_view.channel_tree,
        ):
            tree.clear_tree()
            for guild_id, (guild, channels) in guild_channels.items():
                tree.add_guild(guild, channels)
            tree.add_dm_channels(dm_channels)

    # --- Purge handlers ---

    def _on_scan(self, search_filter: SearchFilter) -> None:
        if self._search_worker:
            self._search_worker.scan(search_filter)

    def _on_scan_result(self, count: int) -> None:
        self._window.purge_view.set_scan_result(count)

    def _on_purge(self, search_filter: SearchFilter) -> None:
        if not self._deletion_worker:
            return

        # Confirm
        if self._settings.confirm_before_delete:
            # Quick scan first
            async def _scan_and_confirm():
                try:
                    counts = await self._search_engine.count_messages(search_filter)
                    total = sum(counts.values())
                    self._bridge.call_on_main_thread(
                        lambda _t=total, _sf=search_filter: self._confirm_and_purge(_t, _sf)
                    )
                except Exception as e:
                    err_msg = str(e)
                    self._bridge.call_on_main_thread(
                        lambda _msg=err_msg: self._window.purge_view.log_view.append_log(
                            "ERROR", _msg
                        )
                    )

            self._bridge.submit(_scan_and_confirm())
        else:
            self._start_purge(search_filter)

    def _confirm_and_purge(self, count: int, search_filter: SearchFilter) -> None:
        if count == 0:
            self._window.purge_view.log_view.append_log(
                "WARNING", "No messages found to delete"
            )
            return

        dialog = ConfirmDeleteDialog(count, self._window)
        if dialog.exec():
            self._start_purge(search_filter)

    def _start_purge(self, search_filter: SearchFilter) -> None:
        self._window.purge_view.set_running(True)
        self._deletion_worker.start_deletion(search_filter)

    def _on_deletion_progress(self, job: DeletionJob) -> None:
        self._window.purge_view.update_progress(job)

    def _on_deletion_complete(self, job: DeletionJob) -> None:
        self._window.purge_view.set_running(False)

        # Save job to database
        async def _save():
            profile = self._profile_manager.active_profile
            if profile:
                job.profile_id = profile.id
            await self._database.save_deletion_job(job)

        self._bridge.submit(_save())

    def _on_pause(self) -> None:
        if self._deletion_worker:
            self._deletion_worker.pause()

    def _on_resume(self) -> None:
        if self._deletion_worker:
            self._deletion_worker.resume()

    def _on_cancel(self) -> None:
        if self._deletion_worker:
            self._deletion_worker.cancel()

    # --- Analytics handler ---

    def _on_compute_analytics(self, search_filter: SearchFilter) -> None:
        if self._analytics_worker:
            # Default filter: all guilds for current user
            if not search_filter.guild_ids and not search_filter.channel_ids:
                guild_ids, channel_ids = (
                    self._window.purge_view.channel_tree.get_selected()
                )
                if not guild_ids and not channel_ids:
                    # Use all guilds
                    async def _get_guilds_and_compute():
                        guilds = await self._client.get_guilds()
                        sf = SearchFilter(guild_ids=[g.id for g in guilds])
                        self._analytics_worker.compute(sf)

                    self._bridge.submit(_get_guilds_and_compute())
                    return

                search_filter = SearchFilter(
                    guild_ids=guild_ids, channel_ids=channel_ids
                )

            self._analytics_worker.compute(search_filter)

    # --- Export handler ---

    def _on_export(self, guild_ids, channel_ids, fmt, path, organize) -> None:
        if not self._export_worker:
            return
        search_filter = SearchFilter(guild_ids=guild_ids, channel_ids=channel_ids)
        export_format = ExportFormat(fmt)
        self._window.export_view.set_running(True)
        self._export_worker.start_export(search_filter, path, export_format, organize)

    def _on_export_complete(self, path: str) -> None:
        self._window.export_view.set_running(False)
        self._window.export_view.set_complete(path)

    # --- Profile handlers ---

    def _on_new_profile(self) -> None:
        dialog = ProfileEditorDialog(parent=self._window)
        if dialog.exec():
            name = dialog.profile_name
            token = dialog.token
            if token:
                async def _create():
                    try:
                        await self._profile_manager.create_profile(
                            name, token, self._rate_limiter
                        )
                        profiles = await self._profile_manager.load_profiles()
                        self._bridge.call_on_main_thread(
                            lambda _p=profiles: self._refresh_profiles(_p)
                        )
                    except Exception as e:
                        err_msg = str(e)
                        self._bridge.call_on_main_thread(
                            lambda _msg=err_msg: ErrorDialog.show_error(
                                "Profile Error", _msg, parent=self._window
                            )
                        )

                self._bridge.submit(_create())

    def _on_edit_profile(self, profile_id: int) -> None:
        profiles = self._window.settings_view._profiles
        profile = next((p for p in profiles if p.id == profile_id), None)
        if not profile:
            return

        dialog = ProfileEditorDialog(profile, parent=self._window)
        if dialog.exec():
            profile.name = dialog.profile_name
            new_token = dialog.token or None

            async def _update():
                try:
                    await self._profile_manager.update_profile(profile, new_token)
                    profiles = await self._profile_manager.load_profiles()
                    self._bridge.call_on_main_thread(
                        lambda _p=profiles: self._refresh_profiles(_p)
                    )
                except Exception as e:
                    err_msg = str(e)
                    self._bridge.call_on_main_thread(
                        lambda _msg=err_msg: ErrorDialog.show_error(
                            "Profile Error", _msg, parent=self._window
                        )
                    )

            self._bridge.submit(_update())

    def _on_delete_profile(self, profile_id: int) -> None:
        async def _delete():
            try:
                await self._profile_manager.delete_profile(profile_id)
                profiles = await self._profile_manager.load_profiles()
                self._bridge.call_on_main_thread(
                    lambda _p=profiles: self._refresh_profiles(_p)
                )
            except Exception as e:
                err_msg = str(e)
                self._bridge.call_on_main_thread(
                    lambda _msg=err_msg: ErrorDialog.show_error(
                        "Profile Error", _msg, parent=self._window
                    )
                )

        self._bridge.submit(_delete())

    def _refresh_profiles(self, profiles: list[Profile]) -> None:
        self._window.login_view.set_profiles(profiles)
        self._window.settings_view.set_profiles(profiles)

    # --- Scheduler handlers ---

    def _on_new_schedule(self) -> None:
        dialog = ScheduleEditorDialog(parent=self._window)
        if dialog.exec():
            job = ScheduledJob(
                name=dialog.job_name,
                cron_expression=dialog.cron_expression,
                enabled=dialog.is_enabled,
                profile_id=(
                    self._profile_manager.active_profile.id
                    if self._profile_manager and self._profile_manager.active_profile
                    else None
                ),
            )
            if self._scheduler_worker:
                self._scheduler_worker.add_job(job)

    def _on_edit_schedule(self, job_id: int) -> None:
        jobs = self._window.scheduler_view._jobs
        job = next((j for j in jobs if j.id == job_id), None)
        if not job:
            return

        dialog = ScheduleEditorDialog(job, parent=self._window)
        if dialog.exec():
            job.name = dialog.job_name
            job.cron_expression = dialog.cron_expression
            job.enabled = dialog.is_enabled
            if self._scheduler_worker:
                self._scheduler_worker.update_job(job)

    def _on_delete_schedule(self, job_id: int) -> None:
        if self._scheduler_worker:
            self._scheduler_worker.remove_job(job_id)

    def _on_toggle_schedule(self, job_id: int, enabled: bool) -> None:
        if self._scheduler_worker:
            self._scheduler_worker.toggle_job(job_id, enabled)

    def _on_run_schedule_now(self, job_id: int) -> None:
        if self._scheduler_worker:
            self._scheduler_worker.run_now(job_id)

    # --- Settings handlers ---

    def _on_settings_changed(self, settings: AppSettings) -> None:
        self._settings = settings
        self._rate_limiter.delete_delay = settings.delete_delay

        if self._theme:
            self._theme.scanline_enabled = settings.scanline_enabled
            self._theme.animation_speed = settings.animation_speed

        if self._window:
            self._window.set_scanline_enabled(settings.scanline_enabled)
            self._window.set_minimize_to_tray(settings.minimize_to_tray)

        # Save to database
        async def _save():
            await self._database.save_all_settings(settings)

        self._bridge.submit(_save())

    def _on_accent_color_changed(self, color: str) -> None:
        if self._theme:
            self._theme.accent_color = color
        self._settings.accent_color = color

    # --- Global log handler ---

    def _on_global_log(self, level: str, message: str) -> None:
        if self._window and hasattr(self._window, "purge_view"):
            self._window.purge_view.log_view.append_log(level, message)

    def shutdown(self) -> None:
        """Clean shutdown."""
        if self._scheduler:
            self._scheduler.stop()
        if self._client:
            self._bridge.submit(self._client.close())
        if self._database:
            self._bridge.submit(self._database.close())
        if self._bridge:
            self._bridge.stop()


def main() -> int:
    """Application entry point."""
    app = NeurowipeApp()
    try:
        return app.run()
    finally:
        app.shutdown()
