"""GUI and plot chrome that follows the system colour scheme.

ARCHITECTURE_V1.md §5.8 asks for system dark mode and for plots that stay
readable when colour is not available. Matplotlib does not follow Qt on its
own; these helpers restyle figures after they are drawn. ``ROOMSCOPE_COLOR_SCHEME``
overrides the system for tests (``dark`` or ``light``).
"""

from __future__ import annotations

import os
from typing import Any

from matplotlib.figure import Figure

ENV_COLOR_SCHEME = "ROOMSCOPE_COLOR_SCHEME"

_DARK = {
    "bg": "#1e1e1e",
    "fg": "#e6e6e6",
    "grid": "#555555",
    "muted": "#8a8a8a",
}
_LIGHT = {
    "bg": "#ffffff",
    "fg": "#222222",
    "grid": "#cccccc",
    "muted": "#666666",
}


def color_scheme() -> str:
    """Return ``dark`` or ``light``."""
    forced = os.environ.get(ENV_COLOR_SCHEME, "").strip().lower()
    if forced in {"dark", "light"}:
        return forced
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return "dark"
    except Exception:
        pass
    return "light"


def plot_colors() -> dict[str, str]:
    return dict(_DARK if color_scheme() == "dark" else _LIGHT)


def style_figure(fig: Figure) -> None:
    """Recolour a drawn figure so axes stay readable on a dark or light canvas."""
    colors = plot_colors()
    bg, fg, grid, muted = colors["bg"], colors["fg"], colors["grid"], colors["muted"]
    fig.patch.set_facecolor(bg)
    for ax in fig.get_axes():
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.title.set_color(fg)
        for spine in ax.spines.values():
            spine.set_color(muted)
        for line in (*ax.get_xgridlines(), *ax.get_ygridlines()):
            line.set_color(grid)
        for text in ax.texts:
            text.set_color(fg)
        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(bg)
            legend.get_frame().set_edgecolor(muted)
            for text in legend.get_texts():
                text.set_color(fg)


def apply_application_chrome(app: Any) -> None:
    """When the system (or override) is dark, give Qt a Fusion dark palette."""
    if color_scheme() != "dark":
        return
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QStyleFactory

    styles = QStyleFactory.keys()
    if "Fusion" in styles:
        app.setStyle("Fusion")
    palette = QPalette()
    bg = QColor("#1e1e1e")
    fg = QColor("#e6e6e6")
    base = QColor("#252526")
    muted = QColor("#3c3c3c")
    accent = QColor("#0e639c")
    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, fg)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, muted)
    palette.setColor(QPalette.ColorRole.Text, fg)
    palette.setColor(QPalette.ColorRole.Button, muted)
    palette.setColor(QPalette.ColorRole.ButtonText, fg)
    palette.setColor(QPalette.ColorRole.ToolTipBase, base)
    palette.setColor(QPalette.ColorRole.ToolTipText, fg)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, fg)
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8a8a8a"))
    app.setPalette(palette)
