"""
The one working session the server keeps.

Kept apart from the HTTP layer: there is no network here, only "take a
dictionary of inputs, run the analysis, give the results back as a
dictionary". Everything the interface does can therefore be tested without
opening a socket.

Deriving the parameters of a borehole takes a fraction of a second, so it runs
inline; there is no background job to follow.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from .. import exporters, forms, render, report, summary
from ..engine import CorrelationAnalysis, CorrelationError
from ..i18n import TRANSLATIONS, warning_text
from .strings import shell_strings

#: Languages the interface offers
LANGS = ("en", "tr")


class Session:
    """The single analysis session the server knows about."""

    def __init__(self, lang: str = "en", theme: str = "light"):
        self.lock = threading.Lock()
        self.lang = lang if lang in LANGS else "en"
        self.theme = theme
        self.analysis: Optional[CorrelationAnalysis] = None
        self.values: Dict[str, Any] = {}

    # ------------------------------------------------------------------ language
    def set_language(self, lang: str) -> str:
        with self.lock:
            self.lang = lang if lang in LANGS else "en"
            return self.lang

    def set_theme(self, theme: str) -> str:
        with self.lock:
            self.theme = "dark" if theme == "dark" else "light"
            return self.theme

    @property
    def t(self) -> dict:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

    def _explain(self, exc: Exception) -> str:
        """An input error in the user's language."""
        if isinstance(exc, CorrelationError):
            return warning_text(self.lang, (exc.key, exc.params))
        return str(exc)

    # ------------------------------------------------------------------ what the page loads with
    def meta(self) -> dict:
        """Everything the interface reads on startup: version, texts, schema."""
        from .. import APP_NAME, __version__
        return {
            "app": APP_NAME,
            "version": __version__,
            "language": self.lang,
            "languages": list(LANGS),
            "strings": shell_strings(self.lang),
            "schema": forms.schema(self.lang),
            "defaults": forms.defaults(self.lang),
            "figures": render.PLOT_KEYS,
            "figure_labels": {key: self.t[f"fig_{key}"] for key in render.PLOT_KEYS},
        }

    def state(self) -> dict:
        with self.lock:
            return {"job": "idle", "has_analysis": self.analysis is not None}

    # ================================================================== analysis
    def analyse(self, values: dict) -> dict:
        """Derives the parameters from the interface's values."""
        try:
            analysis = CorrelationAnalysis(forms.to_config(values))
            analysis.run()
        except CorrelationError as exc:
            raise ValueError(self._explain(exc)) from exc

        with self.lock:
            self.analysis = analysis
            self.values = dict(values)

        return {
            "ok": True,
            "cards": summary.cards(analysis, self.lang),
            "text": summary.results_text(analysis, self.lang),
            "headline": summary.headline(analysis, self.lang),
            "figures": render.available_figures(analysis),
            "warnings": summary.warnings(analysis, self.lang),
            "table": summary.design_table(analysis, self.lang),
            "methods": summary.method_tables(analysis, self.lang),
            "tests": summary.test_tables(analysis, self.lang),
        }

    def _current(self) -> CorrelationAnalysis:
        with self.lock:
            analysis = self.analysis
        if analysis is None:
            raise ValueError(shell_strings(self.lang)["no_results"])
        return analysis

    # ------------------------------------------------------------------ figures
    def plot(self, kind: str) -> bytes:
        """The requested figure as PNG."""
        analysis = self._current()
        return render.figure_to_png(render.analysis_figure(analysis, kind, self.lang, self.theme))

    # ================================================================== report and exports
    def report(self, fmt: str, path: str) -> str:
        """Writes the report in the chosen format; returns the path."""
        analysis = self._current()
        writer = {"pdf": report.export_pdf, "html": report.export_html,
                  "docx": report.export_docx}.get(fmt)
        if writer is None:
            raise ValueError(f"unknown report format: {fmt}")
        writer(path, analysis, self.lang)
        return path

    def export(self, target: str) -> dict:
        """The parameters as a project file of another SlipSurface IQ program."""
        analysis = self._current()
        if target == "settle":
            return exporters.to_settle(analysis)
        if target == "bearing":
            return exporters.to_bearing(analysis)
        raise ValueError(f"unknown export: {target}")

    def export_csv(self, path: str) -> str:
        return exporters.to_csv(self._current(), path)

    # ================================================================== project files
    def project_file(self, values: dict) -> dict:
        """What `Save` downloads."""
        return forms.project_file(values)

    def load_project(self, data: dict) -> dict:
        """Flat interface values from a project file, defaults filling the gaps."""
        if not isinstance(data, dict) or data.get("format") not in (None, forms.FILE_FORMAT):
            raise ValueError(shell_strings(self.lang)["bad_file"])
        return {"ok": True, "values": forms.from_config(data, forms.defaults(self.lang))}
