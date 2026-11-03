"""
Figure production for SlipSurface IQ Correlation.

The interface runs in a browser, so figures are drawn on the server and sent
as PNG. The same functions draw the figures that go into the report, so what
is on screen and what is in the report are the same picture.

Matplotlib is used through the Agg backend: the server needs no display.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure  # noqa: E402

from .plotting import PLOT_KEYS, Plotter, available  # noqa: E402

#: Resolution of the PNGs (enough for the screen, and used by the report)
DPI = 130

__all__ = ["DPI", "PLOT_KEYS", "figure_to_png", "analysis_figure", "available_figures"]


def figure_to_png(fig: Figure, dpi: int = DPI) -> bytes:
    """The figure as PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    return buf.getvalue()


def analysis_figure(analysis, key: str, lang: str = "en", theme: str = "light",
                    size=(10.0, 7.0)) -> Figure:
    """One figure of the analysis."""
    if key not in PLOT_KEYS:
        raise ValueError(f"unknown figure: {key}")
    fig = Figure(figsize=size, dpi=DPI)
    Plotter(analysis, lang, theme).draw(key, fig)
    return fig


def available_figures(analysis=None) -> list:
    """The figures that can be drawn for the analysis just run."""
    return available(analysis) if analysis is not None else list(PLOT_KEYS)
