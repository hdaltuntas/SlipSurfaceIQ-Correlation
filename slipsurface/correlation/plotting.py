"""
The figures of SlipSurface IQ Correlation.

Every figure is drawn on a Matplotlib `Figure` passed in by the caller, so the
same code serves the browser (PNG through `render`) and the report. Nothing
here needs a display.

    profile      the soil column, and the selected parameters of each layer
    spt          N, N60 and (N1)60 with depth
    cpt          qt, fs, u2 and Ic with depth
    sbt          Robertson's (2009) Qtn – Fr chart with the readings
    strength     φ' and cu with depth: every correlation, and the selected value
    state        Dr, and σ'p against σ'v0, with depth
    stiffness    E' / Eu and Vs with depth
    plasticity   Casagrande's chart with the layers
    comparison   every correlation of φ', cu, E and Vs, layer by layer
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from .config import METHOD_COLOURS, PLOT_PALETTE, SOIL_FILL
from .correlations import METHODS, methods_for, reference
from .i18n import TRANSLATIONS
from .plot_style import TITLE_FONT, label_box, style_axis, style_figure
from .summary import fmt, unit

#: The figures, in the order the interface offers them
PLOT_KEYS = ["profile", "spt", "cpt", "sbt", "strength", "state", "stiffness", "plasticity",
             "comparison"]

#: Ic of the zone boundaries on the SBT chart
IC_BOUNDARIES = [1.31, 2.05, 2.60, 2.95, 3.60]

#: Parameters the profile figure writes beside each layer
PROFILE_PARAMS = {"granular": ["gamma", "Dr", "phi", "E", "Vs"],
                  "cohesive": ["gamma", "cu", "phi", "OCR", "Eu", "Cc", "Vs"]}


def available(analysis) -> list:
    """The figures there is something to draw for."""
    res = analysis.results
    layers = res["layers"]

    def has(param):
        return any(lay["params"][param]["value"] is not None for lay in layers)

    keys = ["profile"]
    if res["spt"]:
        keys.append("spt")
    if res["cpt"]:
        keys += ["cpt", "sbt"]
    if has("phi") or has("cu"):
        keys.append("strength")
    if has("Dr") or has("sigma_p"):
        keys.append("state")
    if has("E") or has("Eu") or has("Vs"):
        keys.append("stiffness")
    if any(lay["PI"] is not None for lay in layers):
        keys.append("plasticity")
    keys.append("comparison")
    return keys


class Plotter:
    """Draws the figures of one finished `CorrelationAnalysis`."""

    def __init__(self, analysis, lang: str = "en", theme: str = "light", titles: bool = True):
        self.a = analysis
        self.res = analysis.results
        self.lang = lang if lang in TRANSLATIONS else "en"
        self.L = TRANSLATIONS[self.lang]
        self.theme = theme if theme in ("light", "dark", "paper") else "light"
        # The report writes each figure's name above it; there the figure goes untitled.
        self.titles = titles

    # ------------------------------------------------------------------ entry
    def draw(self, key: str, fig: Figure) -> None:
        if key not in PLOT_KEYS:
            raise ValueError(f"unknown figure: {key}")
        th = style_figure(fig, self.theme)
        getattr(self, f"_{key}")(fig, th)

    # ------------------------------------------------------------------ helpers
    def _title(self, fig, th, key):
        if not self.titles:
            return
        info = self.a.config.get("project_info", {}).get("title", "")
        fig.suptitle(self.L[f"fig_{key}"], color=th["fg"], fontsize=13.5, fontfamily=TITLE_FONT,
                     x=0.02, ha="left")
        if info:
            fig.text(0.98, 0.965, info, color=th["fg_dim"], fontsize=8.5, ha="right",
                     va="center")

    @property
    def depth(self) -> float:
        return self.res["layers"][-1]["bottom"]

    def _depth_axis(self, ax, th, label: bool = True):
        """Depth downwards, with the layer boundaries and the water table."""
        ax.set_ylim(self.depth, 0.0)
        if label:
            ax.set_ylabel(self.L["ax_depth"])
        for layer in self.res["layers"][:-1]:
            ax.axhline(layer["bottom"], color=th["border"], lw=0.9, zorder=1)
        if 0 <= self.a.zw <= self.depth:
            ax.axhline(self.a.zw, color=PLOT_PALETTE["water"], lw=1.1, ls=(0, (6, 3)), zorder=2)
        ax.grid(True, axis="both", color=th["border"], lw=0.6, alpha=0.7)

    def _legend(self, ax, th, **kw):
        kw.setdefault("fontsize", 7.5)
        legend = ax.legend(frameon=True, **kw)
        legend.get_frame().set_facecolor(th["panel"])
        legend.get_frame().set_edgecolor(th["border"])
        for text in legend.get_texts():
            text.set_color(th["fg"])

    def _empty(self, fig, th, key):
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.5, self.L["no_data"], ha="center", va="center", color=th["fg_dim"],
                transform=ax.transAxes, fontsize=11)
        self._title(fig, th, key)

    @staticmethod
    def _colour(param: str, key: str) -> str:
        keys = [m.key for m in methods_for(param)]
        return METHOD_COLOURS[keys.index(key) % len(METHOD_COLOURS)] if key in keys \
            else METHOD_COLOURS[-1]

    def _param_depth(self, ax, th, param: str, log: bool = False) -> bool:
        """Every correlation of one parameter with depth, and the selected value per layer.

        Values from a test are drawn at the test's depth; values that belong to a
        whole layer (the laboratory, the derived ones) across the layer.
        Returns whether anything was drawn.
        """
        drawn, labelled = False, set()
        for rows in (self.res["spt"], self.res["cpt"]):
            points = {}
            for row in rows:
                for key, value in row["methods"].items():
                    if METHODS[key].param == param:
                        points.setdefault(key, ([], []))
                        points[key][0].append(value)
                        points[key][1].append(row["depth"])
            for key, (xs, zs) in points.items():
                marker = "o" if METHODS[key].source == "spt" else "."
                ax.scatter(xs, zs, s=16 if marker == "o" else 12, marker=marker,
                           color=self._colour(param, key), alpha=0.85, zorder=3,
                           label=reference(key, self.lang) if key not in labelled else None)
                labelled.add(key)
                drawn = True
        for lay in self.res["layers"]:
            info = lay["params"][param]
            for key, m in info["methods"].items():
                if METHODS[key].source in ("lab", "derived", "vs"):
                    ax.plot([m["value"]] * 2, [lay["top"], lay["bottom"]], lw=1.4, ls=(0, (4, 2)),
                            color=self._colour(param, key), zorder=3,
                            label=reference(key, self.lang) if key not in labelled else None)
                    labelled.add(key)
                    drawn = True
            if info["value"] is not None:
                ax.plot([info["value"]] * 2, [lay["top"], lay["bottom"]], lw=3.0,
                        color=PLOT_PALETTE["selected"], solid_capstyle="butt", zorder=4,
                        label=self.L["lg_selected"] if "_sel" not in labelled else None)
                labelled.add("_sel")
                drawn = True
        if log:
            ax.set_xscale("log")
        sym = self.L[f"sym_{param}"]
        u = unit(param, self.L)
        ax.set_xlabel(f"{sym} ({u})" if u else sym)
        return drawn

    # ------------------------------------------------------------------ figures
    def _profile(self, fig, th):
        L = self.L
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.grid(False)
        fills = SOIL_FILL[self.theme]
        for lay in self.res["layers"]:
            h = lay["bottom"] - lay["top"]
            ax.add_patch(Rectangle((0.0, lay["top"]), 0.22, h, facecolor=fills[lay["behaviour"]],
                                   edgecolor=th["border"], lw=0.9, zorder=1))
            ax.text(0.11, lay["mid"], f"{lay['name']}\n{lay['uscs']}", ha="center", va="center",
                    fontsize=7.5, color=th["fg"], zorder=3)
            parts = []
            for param in PROFILE_PARAMS[lay["behaviour"]]:
                value = lay["params"][param]["value"]
                if value is not None:
                    u = unit(param, L)
                    parts.append(f"{L['sym_' + param]} = {fmt(param, value)}" + (f" {u}" if u else ""))
            lines = [" · ".join(parts[i:i + 4]) for i in range(0, len(parts), 4)]
            ax.text(0.25, lay["mid"], "\n".join(lines), ha="left", va="center", fontsize=8,
                    color=th["fg"], zorder=3, bbox=label_box(th, 0.85))
        if 0 <= self.a.zw <= self.depth:
            ax.axhline(self.a.zw, xmax=0.22, color=PLOT_PALETTE["water"], lw=1.4, ls=(0, (6, 3)))
            ax.plot([0.2], [self.a.zw], marker="v", color=PLOT_PALETTE["water"], ms=8, zorder=4)
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(self.depth, 0.0)
        ax.set_xticks([])
        ax.set_ylabel(L["ax_depth"])
        ax.spines["bottom"].set_visible(False)
        self._title(fig, th, "profile")

    def _spt(self, fig, th):
        L, rows = self.L, self.res["spt"]
        if not rows:
            return self._empty(fig, th, "spt")
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        self._depth_axis(ax, th)
        z = [r["depth"] for r in rows]
        for key, label, colour, marker in (("N", "lg_n", PLOT_PALETTE["n_field"], "s"),
                                           ("N60", "lg_n60", PLOT_PALETTE["n60"], "o"),
                                           ("N1_60", "lg_n160", PLOT_PALETTE["n160"], "D")):
            ax.plot([r[key] for r in rows], z, marker=marker, ms=5, lw=1.2, color=colour,
                    label=L[label], zorder=3)
        ax.set_xlim(left=0)
        ax.set_xlabel(L["ax_N"])
        ax.xaxis.set_label_position("top")
        ax.xaxis.tick_top()
        self._legend(ax, th, loc="lower left")
        self._title(fig, th, "spt")

    def _cpt(self, fig, th):
        L, rows = self.L, self.res["cpt"]
        if not rows:
            return self._empty(fig, th, "cpt")
        z = np.array([r["depth"] for r in rows])
        axes = fig.subplots(1, 4, sharey=True)
        series = [
            ([r["qt"] / 1000.0 for r in rows], "ax_qt", PLOT_PALETTE["qt"]),
            ([r["fs"] for r in rows], "ax_fs", PLOT_PALETTE["fs"]),
            ([r["u2"] for r in rows], "ax_u", PLOT_PALETTE["u2"]),
            ([r["Ic"] for r in rows], "ax_ic", PLOT_PALETTE["ic"]),
        ]
        for i, (ax, (values, label, colour)) in enumerate(zip(axes, series)):
            style_axis(ax, th)
            self._depth_axis(ax, th, label=i == 0)
            ax.plot(values, z, color=colour, lw=1.3, zorder=3)
            ax.set_xlabel(L[label])
            ax.xaxis.set_label_position("top")
            ax.xaxis.tick_top()
        axes[2].plot([r["u0"] for r in rows], z, color=PLOT_PALETTE["u0"], lw=1.0, ls="--",
                     label=L["lg_u0"])
        self._legend(axes[2], th, loc="lower left")
        ax = axes[3]
        for boundary in IC_BOUNDARIES:
            ax.axvline(boundary, color=th["border"], lw=0.9, zorder=1)
        ax.set_xlim(1.0, 4.0)
        fig.subplots_adjust(wspace=0.08)
        self._title(fig, th, "cpt")

    def _sbt(self, fig, th):
        L, rows = self.L, self.res["cpt"]
        if not rows:
            return self._empty(fig, th, "sbt")
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.set_xscale("log")
        ax.set_yscale("log")
        fr = np.logspace(-1, 1, 200)
        qtn = np.logspace(0, 3, 200)
        F, Q = np.meshgrid(fr, qtn)
        ic = np.sqrt((3.47 - np.log10(Q)) ** 2 + (np.log10(F) + 1.22) ** 2)
        ax.contour(F, Q, ic, levels=IC_BOUNDARIES, colors=th["fg_dim"], linewidths=0.9)
        # zone numbers where each band is widest on the chart
        for zone, (x, y) in {7: (0.2, 500), 6: (0.45, 150), 5: (0.9, 45), 4: (1.8, 11),
                             3: (3.0, 7), 2: (6.5, 2.0)}.items():
            ax.text(x, y, str(zone), fontsize=13, color=th["fg_dim"], ha="center", va="center",
                    fontfamily=TITLE_FONT)
        names = [lay["name"] for lay in self.res["layers"]]
        for index, name in enumerate(names):
            pts = [r for r in rows if r["layer"] == index]
            if pts:
                ax.scatter([r["Fr"] for r in pts], [r["Qtn"] for r in pts], s=18,
                           color=METHOD_COLOURS[index % len(METHOD_COLOURS)], zorder=3,
                           edgecolor=th["panel"], linewidth=0.5, label=name)
        ax.set_xlim(0.1, 10)
        ax.set_ylim(1, 1000)
        ax.set_xlabel(L["ax_fr"])
        ax.set_ylabel(L["ax_qtn"])
        ax.grid(True, which="both", color=th["border"], lw=0.5, alpha=0.6)
        key = "  ".join(f"{z}: {L[f'zone_{z}']}" for z in (2, 3, 4, 5, 6, 7))
        ax.text(0.0, -0.12, key, transform=ax.transAxes, fontsize=7, color=th["fg_dim"],
                wrap=True)
        self._legend(ax, th, loc="upper right")
        self._title(fig, th, "sbt")

    def _depth_panels(self, fig, th, key, params, logs=()):
        panels = [p for p in params
                  if any(lay["params"][p]["value"] is not None for lay in self.res["layers"])]
        if not panels:
            return self._empty(fig, th, key)
        axes = np.atleast_1d(fig.subplots(1, len(panels), sharey=True))
        for i, (ax, param) in enumerate(zip(axes, panels)):
            style_axis(ax, th)
            self._depth_axis(ax, th, label=i == 0)
            self._param_depth(ax, th, param, log=param in logs)
            ax.xaxis.set_label_position("top")
            ax.xaxis.tick_top()
            if ax.get_legend_handles_labels()[0]:
                # below the axes: the depth axis has its numbers on top
                self._legend(ax, th, loc="upper center", bbox_to_anchor=(0.5, -0.02),
                             fontsize=6.5, ncol=1)
        fig.subplots_adjust(wspace=0.1)
        self._title(fig, th, key)

    def _strength(self, fig, th):
        self._depth_panels(fig, th, "strength", ["phi", "cu"])

    def _state(self, fig, th):
        self._depth_panels(fig, th, "state", ["Dr", "sigma_p"])
        # σ'v0 beside σ'p, so the overconsolidation can be read off
        for ax in fig.axes:
            if ax.get_xlabel().startswith(self.L["sym_sigma_p"]):
                z = np.linspace(0.0, self.depth, 80)
                ax.plot([self.a.profile.stresses(d)["sigma_eff"] for d in z], z,
                        color=th["fg_dim"], lw=1.0, ls="--", label="σ'v0")
                self._legend(ax, th, loc="upper center", bbox_to_anchor=(0.5, -0.02),
                             fontsize=6.5, ncol=1)

    def _stiffness(self, fig, th):
        self._depth_panels(fig, th, "stiffness", ["E", "Eu", "Vs"])

    def _plasticity(self, fig, th):
        L = self.L
        layers = [lay for lay in self.res["layers"] if lay["PI"] is not None]
        if not layers:
            return self._empty(fig, th, "plasticity")
        ax = fig.add_subplot(111)
        style_axis(ax, th)
        ax.grid(True, color=th["border"], lw=0.6)
        top = max(100.0, max(lay["LL"] for lay in layers) * 1.15)
        ll = np.linspace(0, top, 200)
        ax.plot(ll, np.maximum(0.73 * (ll - 20.0), 0), color=th["fg"], lw=1.3,
                label=L["lg_a_line"])
        ax.plot(ll, np.maximum(0.9 * (ll - 8.0), 0), color=th["fg_dim"], lw=1.0, ls="--",
                label=L["lg_u_line"])
        ax.axvline(50.0, color=th["border"], lw=1.0)
        ax.fill_between([12.0, 25.5], [4, 4], [7, 7], color=th["border"], alpha=0.6, lw=0)
        for text, (x, y) in {"CL": (35, 25), "CH": (70, 50), "ML": (35, 5), "MH": (75, 18),
                             "CL-ML": (18, 5.5)}.items():
            ax.text(x, y, text, fontsize=10, color=th["fg_dim"], ha="center", va="center",
                    fontfamily=TITLE_FONT)
        for lay in layers:
            colour = METHOD_COLOURS[lay["index"] % len(METHOD_COLOURS)]
            ax.scatter([lay["LL"]], [lay["PI"]], s=46, color=colour, zorder=4,
                       edgecolor=th["panel"], linewidth=0.8)
            ax.annotate(f"{lay['name']} ({lay['uscs']})", (lay["LL"], lay["PI"]),
                        xytext=(8, 4), textcoords="offset points", fontsize=8, color=th["fg"],
                        bbox=label_box(th, 0.85))
        ax.set_xlim(0, top)
        ax.set_ylim(0, max(60.0, top * 0.75))
        ax.set_xlabel(L["ax_LL"])
        ax.set_ylabel(L["ax_PI"])
        self._legend(ax, th, loc="upper left")
        self._title(fig, th, "plasticity")

    def _comparison(self, fig, th):
        L = self.L
        layers = self.res["layers"]
        # the parameters where the correlations actually disagree: two or more in a layer
        params = [p for p in ("phi", "cu", "E", "Vs", "Dr", "Cc", "sigma_p")
                  if any(len(lay["params"][p]["methods"]) > 1 for lay in layers)][:4]
        if not params:
            return self._empty(fig, th, "comparison")
        axes = np.atleast_1d(fig.subplots(len(params), 1))
        names = [f"{lay['index'] + 1}. {lay['name']}" for lay in layers]
        for ax, param in zip(axes, params):
            style_axis(ax, th)
            labelled = set()
            for y, lay in enumerate(layers):
                info = lay["params"][param]
                for key, m in info["methods"].items():
                    ax.scatter([m["value"]], [y], s=28, color=self._colour(param, key), zorder=3,
                               label=reference(key, self.lang) if key not in labelled else None)
                    labelled.add(key)
                if info["value"] is not None:
                    ax.scatter([info["value"]], [y], s=90, marker="D", facecolor="none",
                               edgecolor=PLOT_PALETTE["selected"], linewidth=1.6, zorder=4,
                               label=L["lg_selected"] if "_sel" not in labelled else None)
                    labelled.add("_sel")
            ax.set_yticks(range(len(layers)))
            ax.set_yticklabels(names, fontsize=7.5)
            ax.set_ylim(len(layers) - 0.5, -0.5)
            u = unit(param, L)
            ax.set_xlabel(f"{L['sym_' + param]} ({u})" if u else L["sym_" + param], fontsize=8.5)
            # beside the axes, where it hides no point
            self._legend(ax, th, loc="upper left", bbox_to_anchor=(1.01, 1.05), fontsize=6.5)
        fig.subplots_adjust(right=0.7, hspace=0.75)
        self._title(fig, th, "comparison")
