"""MainWindow — Frameless shell with sidebar navigation, tray, and view management."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from ..constants import (
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_WIDTH,
    TITLE_BAR_HEIGHT,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from ..theme.colors import Colors
from .dashboard_view import DashboardView
from .export_view import ExportView
from .login_view import LoginView
from .purge_view import PurgeView
from .scheduler_view import SchedulerView
from .settings_view import SettingsView
from .widgets.glow_label import GlowLabel
from .widgets.scanline_overlay import ScanlineOverlay
from .widgets.status_bar import StatusBar

logger = logging.getLogger("neurowipe.main_window")


class TitleBar(QWidget):
    """Custom frameless title bar with drag support and window controls."""

    close_requested = Signal()
    minimize_requested = Signal()
    maximize_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self._drag_pos: QPoint | None = None

        self.setStyleSheet(f"""
            TitleBar {{
                background-color: {Colors.TITLEBAR_BG};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        # Logo text
        self._title = GlowLabel(
            "NEUROWIPE", Colors.CYAN, font_size=11, glow_radius=6
        )
        layout.addWidget(self._title)

        layout.addStretch()

        # Window buttons
        btn_style = """
            QPushButton {{
                background: transparent;
                border: none;
                color: {color};
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """

        self._min_btn = QPushButton("\u2500")
        self._min_btn.setFixedSize(32, 28)
        self._min_btn.setStyleSheet(
            btn_style.format(color=Colors.TEXT_SECONDARY, hover_bg=Colors.BG_HOVER)
        )
        self._min_btn.clicked.connect(self.minimize_requested.emit)
        layout.addWidget(self._min_btn)

        self._max_btn = QPushButton("\u25a1")
        self._max_btn.setFixedSize(32, 28)
        self._max_btn.setStyleSheet(
            btn_style.format(color=Colors.TEXT_SECONDARY, hover_bg=Colors.BG_HOVER)
        )
        self._max_btn.clicked.connect(self.maximize_requested.emit)
        layout.addWidget(self._max_btn)

        self._close_btn = QPushButton("\u2716")
        self._close_btn.setFixedSize(32, 28)
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.ERROR};
                color: white;
            }}
        """)
        self._close_btn.clicked.connect(self.close_requested.emit)
        layout.addWidget(self._close_btn)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.maximize_requested.emit()


class SidebarButton(QPushButton):
    """Navigation button for the sidebar."""

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_text = icon_text
        self._label = label
        self._active = False
        self.setText(f" {icon_text}  {label}")
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def _apply_style(self) -> None:
        if self._active:
            self.setStyleSheet(f"""
                SidebarButton {{
                    background-color: {Colors.SIDEBAR_ACTIVE};
                    border: none;
                    border-left: 3px solid {Colors.CYAN};
                    color: {Colors.CYAN};
                    text-align: left;
                    padding-left: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                SidebarButton {{
                    background: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    color: {Colors.TEXT_SECONDARY};
                    text-align: left;
                    padding-left: 12px;
                    font-size: 12px;
                }}
                SidebarButton:hover {{
                    background-color: {Colors.SIDEBAR_HOVER};
                    color: {Colors.TEXT_PRIMARY};
                }}
            """)

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()


class Sidebar(QWidget):
    """Navigation sidebar with icon buttons."""

    page_selected = Signal(int)

    PAGES = [
        ("\u2302", "Login"),
        ("\u2620", "Purge"),
        ("\u2261", "Analytics"),
        ("\u21e9", "Export"),
        ("\u23f0", "Scheduler"),
        ("\u2699", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {Colors.SIDEBAR_BG};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)

        self._buttons: list[SidebarButton] = []

        for i, (icon, label) in enumerate(self.PAGES):
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda _, idx=i: self._on_click(idx))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

        # About button at bottom
        about_btn = SidebarButton("\u24d8", "About")
        about_btn.clicked.connect(lambda: self.page_selected.emit(-1))
        layout.addWidget(about_btn)

        self._set_active(0)

    def _on_click(self, index: int) -> None:
        self._set_active(index)
        self.page_selected.emit(index)

    def _set_active(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)

    def set_page(self, index: int) -> None:
        self._set_active(index)


class MainWindow(QMainWindow):
    """Frameless main window with sidebar navigation and system tray."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEUROWIPE")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(f"background-color: {Colors.BG_DARKEST};")

        self._minimize_to_tray = True

        # Set application icon
        import pathlib
        _icon_path = str(pathlib.Path(__file__).resolve().parent.parent / "resources" / "icons" / "app_icon.jpg")
        self._app_icon = QIcon(QPixmap(_icon_path))
        self.setWindowIcon(self._app_icon)

        self._setup_ui()
        self._setup_tray()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar()
        self._title_bar.close_requested.connect(self._on_close)
        self._title_bar.minimize_requested.connect(self.showMinimized)
        self._title_bar.maximize_requested.connect(self._toggle_maximize)
        root_layout.addWidget(self._title_bar)

        # Body: sidebar + content
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_selected.connect(self._on_page_selected)
        body_layout.addWidget(self._sidebar)

        # Content stack
        self._stack = QStackedWidget()
        body_layout.addWidget(self._stack)

        root_layout.addWidget(body, 1)

        # Status bar
        self._status_bar = StatusBar()
        root_layout.addWidget(self._status_bar)

        # Create views
        self._login_view = LoginView()
        self._purge_view = PurgeView()
        self._dashboard_view = DashboardView()
        self._export_view = ExportView()
        self._scheduler_view = SchedulerView()
        self._settings_view = SettingsView()

        self._stack.addWidget(self._login_view)   # 0
        self._stack.addWidget(self._purge_view)    # 1
        self._stack.addWidget(self._dashboard_view)  # 2
        self._stack.addWidget(self._export_view)   # 3
        self._stack.addWidget(self._scheduler_view)  # 4
        self._stack.addWidget(self._settings_view)  # 5

        # Scanline overlay
        self._scanline = ScanlineOverlay(central)
        self._scanline.raise_()

    def _setup_tray(self) -> None:
        """Set up system tray icon and menu."""
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(self._app_icon)
        self._tray_icon.setToolTip("NEUROWIPE")

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_scanline"):
            self._scanline.setGeometry(self.centralWidget().rect())

    # --- Properties ---

    @property
    def login_view(self) -> LoginView:
        return self._login_view

    @property
    def purge_view(self) -> PurgeView:
        return self._purge_view

    @property
    def dashboard_view(self) -> DashboardView:
        return self._dashboard_view

    @property
    def export_view(self) -> ExportView:
        return self._export_view

    @property
    def scheduler_view(self) -> SchedulerView:
        return self._scheduler_view

    @property
    def settings_view(self) -> SettingsView:
        return self._settings_view

    @property
    def status_bar_widget(self) -> StatusBar:
        return self._status_bar

    @property
    def scanline_overlay(self) -> ScanlineOverlay:
        return self._scanline

    # --- Navigation ---

    def _on_page_selected(self, index: int) -> None:
        if index == -1:
            # About dialog
            from .dialogs.about_dialog import AboutDialog
            AboutDialog(self).exec()
            return
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    def show_login(self) -> None:
        self._stack.setCurrentIndex(0)
        self._sidebar.set_page(0)

    def show_purge(self) -> None:
        self._stack.setCurrentIndex(1)
        self._sidebar.set_page(1)

    def show_dashboard(self) -> None:
        self._stack.setCurrentIndex(2)
        self._sidebar.set_page(2)

    # --- Window controls ---

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _on_close(self) -> None:
        if self._minimize_to_tray:
            self.hide()
            if self._tray_icon.isVisible():
                self._tray_icon.showMessage(
                    "NEUROWIPE",
                    "Running in background. Scheduler is still active.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
        else:
            QApplication.quit()

    def _show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def set_minimize_to_tray(self, enabled: bool) -> None:
        self._minimize_to_tray = enabled

    def set_scanline_enabled(self, enabled: bool) -> None:
        self._scanline.enabled = enabled
        if enabled:
            self._scanline.start()
        else:
            self._scanline.stop()

    def closeEvent(self, event):
        """Override close event for tray behavior."""
        if self._minimize_to_tray and self._tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
