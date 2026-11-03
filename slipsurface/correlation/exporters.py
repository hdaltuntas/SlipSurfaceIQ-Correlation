"""
The parameters sent on: project files for the other SlipSurface IQ programs, and the
parameter table as CSV.

    SlipSurface IQ Settle    γ, γsat, E, ν, Cc, Cr, e0, OCR, cv, Cα of every layer, and
                     the water table. Settle takes the undrained modulus of a
                     cohesive layer, so ν = 0.5 there.
    SlipSurface IQ Bearing   γ, γsat, c', φ', cu, E, ν of every layer, and the water
                     table. c' is set to zero: none of the correlations gives
                     it, and zero is the safe side.

Only the soil goes across: the foundation, the loads and the options keep the
receiving program's defaults, since a project file of theirs fills what it does
not carry from them. A parameter that could not be derived is written as zero,
which the receiving program points out when it is needed.
"""

from __future__ import annotations

import csv
from typing import Any, Dict, List

from .config import PARAM_UNITS, PARAMS

__all__ = ["to_settle", "to_bearing", "parameter_rows", "to_csv", "SETTLE_FORMAT",
           "BEARING_FORMAT"]

SETTLE_FORMAT = "slipsurface-settle"
BEARING_FORMAT = "slipsurface-bearing"
VERSION = "0.1"


def _v(layer: dict, param: str, default: float = 0.0) -> float:
    value = layer["params"][param]["value"]
    return float(value) if value is not None else float(default)


def _common(analysis) -> Dict[str, Any]:
    info = analysis.config.get("project_info", {})
    return {"project_info": {"title": info.get("title", ""), "analyst": info.get("analyst", "")},
            "groundwater": {"depth": analysis.zw, "gamma_water": analysis.gw}}


def _thickness(layer: dict) -> float:
    return round(layer["bottom"] - layer["top"], 4)


def to_settle(analysis) -> Dict[str, Any]:
    """A SlipSurface IQ Settle project file with this profile."""
    layers = []
    for lay in analysis.results["layers"]:
        clay = lay["behaviour"] == "cohesive"
        layers.append({
            "name": lay["name"], "thickness": _thickness(lay), "behaviour": lay["behaviour"],
            "gamma": round(_v(lay, "gamma"), 2), "gamma_sat": round(_v(lay, "gamma_sat"), 2),
            "E": round(_v(lay, "Eu" if clay else "E"), 2),
            "nu": 0.5 if clay else analysis.nu["granular"],
            "Cc": round(_v(lay, "Cc"), 4) if clay else 0.0,
            "Cr": round(_v(lay, "Cr"), 4) if clay else 0.0,
            "e0": round(_v(lay, "e0", 1.0 if clay else 0.6), 3),
            "OCR": round(max(_v(lay, "OCR", 1.0), 1.0), 3) if clay else 1.0,
            "cv": round(_v(lay, "cv"), 3) if clay else 0.0,
            "Calpha": round(_v(lay, "Calpha"), 5) if clay else 0.0,
            "drainage": "double",
        })
    return {"format": SETTLE_FORMAT, "version": VERSION, **_common(analysis),
            "soil_profile": layers}


def to_bearing(analysis) -> Dict[str, Any]:
    """A SlipSurface IQ Bearing project file with this profile."""
    layers = []
    for lay in analysis.results["layers"]:
        clay = lay["behaviour"] == "cohesive"
        layers.append({
            "name": lay["name"], "thickness": _thickness(lay), "behaviour": lay["behaviour"],
            "gamma": round(_v(lay, "gamma"), 2), "gamma_sat": round(_v(lay, "gamma_sat"), 2),
            "c": 0.0, "phi": round(_v(lay, "phi"), 1),
            "cu": round(_v(lay, "cu"), 1) if clay else 0.0,
            "E": round(_v(lay, "Eu" if clay else "E"), 2),
            "nu": analysis.nu[lay["behaviour"]],
        })
    return {"format": BEARING_FORMAT, "version": VERSION, **_common(analysis),
            "soil_profile": layers}


def parameter_rows(analysis) -> List[List[Any]]:
    """The selected parameters as a table: one row per layer, a header first."""
    header = ["layer", "top (m)", "bottom (m)", "behaviour", "USCS"] + \
        [f"{p} ({PARAM_UNITS[p]})" if PARAM_UNITS[p] else p for p in PARAMS]
    rows = [header]
    for lay in analysis.results["layers"]:
        rows.append([lay["name"], lay["top"], lay["bottom"], lay["behaviour"], lay["uscs"]]
                    + [("" if lay["params"][p]["value"] is None
                        else f"{lay['params'][p]['value']:.6g}") for p in PARAMS])
    return rows


def to_csv(analysis, path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(parameter_rows(analysis))
    return path
