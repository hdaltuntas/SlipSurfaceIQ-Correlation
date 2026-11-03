"""
Results as text, as summary cards and as tables.

Both the browser interface and the command line show the same thing: the
headline numbers as a row of cards, the selected parameters of every layer as
a table, and the full account of the analysis as text. Assembling them here
keeps that promise without either side copying the other's wording, and it
needs no interface toolkit at all — pass a finished analysis and a language
code.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .config import PARAM_UNITS, PARAMS
from .correlations import METHODS, reference
from .i18n import TRANSLATIONS, warning_text

#: Card order, as the interface lays them out
CARD_KEYS = ["layers", "spt", "cpt", "vs", "methods", "params", "combine", "warnings"]

#: Decimals of each parameter; "e" for scientific notation
DECIMALS = {"gamma": 1, "gamma_sat": 1, "e0": 3, "Dr": 0, "phi": 1, "cu": 1, "sigma_p": 0,
            "OCR": 2, "K0": 2, "E": 1, "Eu": 1, "M": 1, "Cc": 3, "Cr": 3, "Calpha": 4,
            "cv": 2, "Vs": 0, "G0": 1, "k": "e"}


def _lang(lang: str) -> dict:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def fmt(param: str, value: Optional[float]) -> str:
    """One parameter value, to the precision it deserves."""
    if value is None or not math.isfinite(value):
        return "—"
    decimals = DECIMALS.get(param, 2)
    if decimals == "e":
        return f"{value:.2e}"
    return f"{value:.{decimals}f}"


def unit(param: str, L: dict) -> str:
    return L["unit_m2yr"] if param == "cv" else PARAM_UNITS[param]


def how_text(info: dict, lang: str = "en") -> str:
    """Where a selected value came from."""
    L = _lang(lang)
    how = info.get("how") or ""
    if how in METHODS:
        return reference(how, lang)
    if how == "combined":
        return f"{L['how_combined']} ({len(info['methods'])})"
    if how in ("input", "typical"):
        return L[f"how_{how}"]
    return "—"


def range_text(param: str, info: dict) -> str:
    if info.get("min") is None or len(info.get("methods") or {}) < 2:
        return ""
    return f"{fmt(param, info['min'])} – {fmt(param, info['max'])}"


def shown_params(analysis) -> List[str]:
    """The parameters that have a value in at least one layer."""
    layers = analysis.results["layers"]
    return [p for p in PARAMS if any(lay["params"][p]["value"] is not None for lay in layers)]


def zone_text(L: dict, zone) -> str:
    return f"{zone} · {L[f'zone_{zone}']}" if zone else "—"


def cards(analysis, lang: str = "en") -> List[dict]:
    """The headline numbers: how much was tested and how much came of it."""
    L = _lang(lang)
    res = analysis.results
    counts = res["counts"]
    depth = res["layers"][-1]["bottom"] if res["layers"] else 0.0
    out = []

    def card(key, value, sub="", state=""):
        out.append({"key": key, "title": L[f"card_{key}"], "value": value, "sub": sub,
                    "state": state})

    card("layers", str(counts["layers"]), L["card_depth"].format(d=depth))
    for kind in ("spt", "cpt", "vs"):
        card(kind, str(counts[kind]) if counts[kind] else L["card_none"], "",
             "" if counts[kind] else "na")
    card("methods", str(counts["methods"]))
    card("params", str(counts["params"]))
    card("combine", L[f"combine_{analysis.combine}"].split(" (")[0],
         f"{len(analysis.chosen)} ×" if analysis.chosen else "")
    n_warn = len(res["warnings"])
    card("warnings", str(n_warn) if n_warn else L["card_ok"], "", "bad" if n_warn else "ok")
    return out


def design_table(analysis, lang: str = "en") -> dict:
    """The selected parameters: one row per layer, one column per parameter."""
    L = _lang(lang)
    params = shown_params(analysis)
    columns = [L["head_layer"], "USCS"] + \
        [f"{L['sym_' + p]} ({unit(p, L)})" if unit(p, L) else L["sym_" + p] for p in params]
    rows = []
    for lay in analysis.results["layers"]:
        rows.append([f"{lay['index'] + 1}. {lay['name']}", lay["uscs"]]
                    + [fmt(p, lay["params"][p]["value"]) for p in params])
    return {"columns": columns, "rows": rows}


def method_tables(analysis, lang: str = "en") -> List[dict]:
    """For every layer, every correlation that gave a value and what it gave."""
    L = _lang(lang)
    out = []
    for lay in analysis.results["layers"]:
        rows = []
        for p in PARAMS:
            info = lay["params"][p]
            if info["value"] is None:
                continue
            rows.append([f"{L['sym_' + p]}", f"{fmt(p, info['value'])} {unit(p, L)}".strip(),
                         how_text(info, lang), "", "", ""])
            for key, m in info["methods"].items():
                method = METHODS[key]
                rows.append(["", fmt(p, m["value"]), reference(key, lang),
                             L[f"source_{method.source}"], str(m["n"]), method.formula])
        out.append({
            "title": L["res_layer"].format(i=lay["index"] + 1, name=lay["name"],
                                           behaviour=L[f"behaviour_{lay['behaviour']}"].lower(),
                                           top=lay["top"], bottom=lay["bottom"], uscs=lay["uscs"]),
            "columns": [L["head_param"], L["head_value"], L["head_ref"], L["head_source"],
                        L["head_n"], L["head_formula"]],
            "rows": rows,
        })
    return out


def _n(value, fmt_: str = ".1f") -> str:
    return "—" if value is None else format(value, fmt_)


def test_tables(analysis, lang: str = "en") -> List[dict]:
    """The field tests as processed: stresses, corrections, normalised values."""
    L = _lang(lang)
    res = analysis.results
    names = [lay["name"] for lay in res["layers"]]
    out = []
    if res["spt"]:
        out.append({
            "title": "SPT",
            "columns": [L["head_depth"], L["head_layer"], "N", "σ'v0 (kPa)", "CR", "N60", "CN",
                        "(N1)60", "Dr (%)", "φ' (°)", "cu (kPa)", "Vs (m/s)"],
            "rows": [[f"{r['depth']:.2f}", names[r["layer"]], f"{r['N']:.0f}",
                      f"{r['sigma_eff']:.1f}", f"{r['CR']:.2f}", f"{r['N60']:.1f}",
                      f"{r['CN']:.2f}", f"{r['N1_60']:.1f}", _n(r["selected"].get("Dr"), ".0f"),
                      _n(r["selected"].get("phi")), _n(r["selected"].get("cu")),
                      _n(r["selected"].get("Vs"), ".0f")] for r in res["spt"]],
        })
    if res["cpt"]:
        out.append({
            "title": "CPT",
            "columns": [L["head_depth"], L["head_layer"], "qt (MPa)", "fs (kPa)", "u2 (kPa)",
                        "σ'v0 (kPa)", "Fr (%)", "Bq", "Qtn", "Ic", L["head_zone"], "γ (kN/m³)",
                        "Dr (%)", "φ' (°)", "cu (kPa)", "Vs (m/s)"],
            "rows": [[f"{r['depth']:.2f}", names[r["layer"]], f"{r['qt'] / 1000:.2f}",
                      f"{r['fs']:.1f}", f"{r['u2']:.1f}", f"{r['sigma_eff']:.1f}",
                      f"{r['Fr']:.2f}", f"{r['Bq']:.2f}", f"{r['Qtn']:.1f}", f"{r['Ic']:.2f}",
                      str(r["zone"]), _n(r["selected"].get("gamma")),
                      _n(r["selected"].get("Dr"), ".0f"), _n(r["selected"].get("phi")),
                      _n(r["selected"].get("cu")), _n(r["selected"].get("Vs"), ".0f")]
                     for r in res["cpt"]],
        })
    if res["vs"]:
        out.append({
            "title": "Vs",
            "columns": [L["head_depth"], L["head_layer"], "Vs (m/s)"],
            "rows": [[f"{r['depth']:.2f}", names[r["layer"]], f"{r['Vs']:.0f}"]
                     for r in res["vs"]],
        })
    return out


def results_text(analysis, lang: str = "en") -> str:
    """The whole analysis as text, in the chosen language."""
    L = _lang(lang)
    a, res = analysis, analysis.results
    layers = res["layers"]
    counts = res["counts"]
    lines = [L["res_title"], "-" * 78,
             L["res_site"].format(zw=a.zw, gw=a.gw, d=layers[-1]["bottom"], n=len(layers)),
             L["res_tests"].format(spt=counts["spt"], cpt=counts["cpt"], vs=counts["vs"])]
    if counts["spt"]:
        s = a.spt
        first = res["spt"][0]
        lines.append(L["res_spt"].format(er=s["energy_ratio"], cb=first["CB"], cs=first["CS"],
                                         cn=L[f"cn_{s['cn_method']}"], cnmax=s["cn_max"]))
    if counts["cpt"]:
        lines.append(L["res_cpt"].format(a=a.cpt["area_ratio"], nkt=a.cpt["Nkt"],
                                         ndu=a.cpt["Ndu"]))
    lines.append(L["res_combine"].format(how=L[f"combine_{a.combine}"]))

    for lay in layers:
        lines += ["", L["res_layer"].format(i=lay["index"] + 1, name=lay["name"],
                                            behaviour=L[f"behaviour_{lay['behaviour']}"].lower(),
                                            top=lay["top"], bottom=lay["bottom"], uscs=lay["uscs"]),
                  "  " + L["res_layer_stress"].format(z=lay["mid"], sv=lay["sigma_v"],
                                                      u0=lay["u0"], se=lay["sigma_eff"]),
                  "  " + L["res_layer_tests"].format(
                      spt=lay["n_spt"], n60=_n(lay["N60"]), n160=_n(lay["N1_60"]),
                      cpt=lay["n_cpt"], ic=_n(lay["Ic"], ".2f"), zone=zone_text(L, lay["zone"]),
                      vs=lay["n_vs"])]
        if lay["PI"] is not None or lay["w"] is not None:
            lines.append("  " + L["res_index"].format(
                LL=_n(lay["LL"], ".0f"), PL=_n(lay["PL"], ".0f"), PI=_n(lay["PI"], ".0f"),
                w=_n(lay["w"], ".1f"), LI=_n(lay["LI"], ".2f")))
        for p in PARAMS:
            info = lay["params"][p]
            if info["value"] is None:
                continue
            spread = range_text(p, info)
            lines.append(f"    {L['sym_' + p]:<6}{fmt(p, info['value']):>11} {unit(p, L):<7}"
                         f"{how_text(info, lang)}" + (f"   [{spread}]" if spread else ""))

    if res["warnings"]:
        lines += ["", L["warnings_title"]]
        lines += ["  • " + warning_text(lang, w) for w in res["warnings"]]
    return "\n".join(lines)


def warnings(analysis, lang: str = "en") -> List[str]:
    return [warning_text(lang, w) for w in analysis.results.get("warnings", [])]


def headline(analysis, lang: str = "en") -> str:
    """One line for the status bar."""
    L = _lang(lang)
    c = analysis.results["counts"]
    return (f"{c['layers']} {L['card_layers'].lower()} · {c['params']} "
            f"{L['card_params'].lower()} · {c['methods']} {L['card_methods'].lower()}")
