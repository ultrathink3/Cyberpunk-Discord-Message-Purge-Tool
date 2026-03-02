"""Chart theme configuration for pyqtgraph with cyberpunk neon colors."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtGui import QColor, QFont

from ...theme.colors import Colors


def apply_chart_theme() -> None:
    """Apply cyberpunk theme to pyqtgraph globally."""
    pg.setConfigOptions(
        background=QColor(Colors.BG_CARD),
        foreground=QColor(Colors.TEXT_PRIMARY),
        antialias=True,
    )


def style_plot_widget(pw: pg.PlotWidget) -> None:
    """Apply cyberpunk styling to a PlotWidget."""
    pw.setBackground(QColor(Colors.BG_CARD))

    plot = pw.getPlotItem()
    if plot is None:
        return

    # Axis styling
    font = QFont("Share Tech Mono", 9)
    for axis_name in ("bottom", "left"):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen(color=Colors.BORDER, width=1))
        axis.setTextPen(pg.mkPen(color=Colors.TEXT_SECONDARY))
        axis.setTickFont(font)
        axis.label.setFont(font)

    # Grid
    plot.showGrid(x=True, y=True, alpha=0.1)

    # Remove top/right axes
    plot.hideAxis("top")
    plot.hideAxis("right")


def get_neon_pen(
    color: str = Colors.CYAN, width: float = 2.0
) -> pg.mkPen:
    """Create a neon-colored pen."""
    return pg.mkPen(color=color, width=width)


def get_neon_brush(color: str = Colors.CYAN, alpha: int = 80) -> pg.mkBrush:
    """Create a semi-transparent neon brush."""
    qc = QColor(color)
    qc.setAlpha(alpha)
    return pg.mkBrush(qc)


# Neon color cycle for multiple series
CHART_COLORS = [
    Colors.CYAN,
    Colors.MAGENTA,
    Colors.ELECTRIC_PURPLE,
    Colors.SUCCESS,
    Colors.WARNING,
    "#ff6644",
    "#44ff66",
    "#6644ff",
]
