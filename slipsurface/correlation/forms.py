"""
Input schema and readers for SlipSurface IQ Correlation.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``water_depth``, ``er``, ``method_phi`` …) are the ones
the interface uses; the nested keys of the configuration
(``groundwater.depth``, ``spt.energy_ratio``, ``options.methods.phi`` …) are
the ones the engine and the ``.correlation`` project files use. `to_config()`
and `from_config()` convert between the two.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .config import BEHAVIOURS, CN_METHODS, COMBINE, DEFAULT_CONFIG, PARAMS, SAMPLERS
from .correlations import methods_for, reference
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "slipsurface-correlation"
FILE_VERSION = "0.1"

#: The tables of the project, as (flat key = configuration key, columns)
TABLES = ["soil_profile", "spt_tests", "cpt_tests", "vs_tests"]


def _t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# --------------------------------------------------------------------------- #
#  Schema data structures
# --------------------------------------------------------------------------- #

@dataclass
class Field:
    """One input field."""
    key: str
    label: str
    kind: str = "number"                     # number | text | check | select
    default: Any = 0.0
    unit: str = ""
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    decimals: int = 2
    options: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Only what the browser needs; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        return {k: v for k, v in asdict(self).items()
                if k in keep or v not in ("", None, [], 0.0)}


@dataclass
class Group:
    """A titled set of fields."""
    title: str
    fields: List[Field]
    note: str = ""

    def to_dict(self) -> dict:
        d = {"title": self.title, "fields": [f.to_dict() for f in self.fields]}
        if self.note:
            d["note"] = self.note
        return d


def _num(key, label, default, lo=None, hi=None, unit="", dec=2, step=None):
    return Field(key, label, "number", default, unit, lo, hi, step, dec)


def _select(key, label, default, options):
    return Field(key, label, "select", default,
                 options=[{"value": v, "label": t} for v, t in options])


def _text(key, label, default=""):
    return Field(key, label, "text", default)


def _choices(lang: str, prefix: str, values: List[str]):
    return [(value, _t(lang, f"{prefix}_{value}")) for value in values]


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #

def project_groups(lang: str = "en") -> List[Group]:
    info = DEFAULT_CONFIG["project_info"]
    w = DEFAULT_CONFIG["groundwater"]
    return [
        Group(_t(lang, "group_project"), [
            _text("title", _t(lang, "title_label"), info["title"]),
            _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
        ]),
        Group(_t(lang, "group_water"), [
            _num("water_depth", _t(lang, "water_depth_label"), w["depth"], 0, 500, "m", 2, 0.1),
            _num("gamma_water", _t(lang, "gamma_w_label"), w["gamma_water"], 9, 11, "kN/m³",
                 2, 0.01),
        ]),
    ]


def test_groups(lang: str = "en") -> List[Group]:
    s = DEFAULT_CONFIG["spt"]
    c = DEFAULT_CONFIG["cpt"]
    return [
        Group(_t(lang, "group_spt"), [
            _num("er", _t(lang, "er_label"), s["energy_ratio"], 20, 120, "%", 0, 5),
            _num("borehole", _t(lang, "borehole_label"), s["borehole"], 50, 300, "mm", 0, 5),
            _select("sampler", _t(lang, "sampler_label"), s["sampler"],
                    _choices(lang, "sampler", SAMPLERS)),
            _num("stickup", _t(lang, "stickup_label"), s["stickup"], 0, 10, "m", 2, 0.1),
            _select("cn_method", _t(lang, "cn_method_label"), s["cn_method"],
                    _choices(lang, "cn", CN_METHODS)),
            _num("cn_max", _t(lang, "cn_max_label"), s["cn_max"], 1, 3, "", 2, 0.05),
        ], note=_t(lang, "spt_note")),
        Group(_t(lang, "group_cpt"), [
            _num("area_ratio", _t(lang, "area_ratio_label"), c["area_ratio"], 0.5, 1, "", 2, 0.01),
            _num("Nkt", _t(lang, "nkt_label"), c["Nkt"], 5, 30, "", 1, 0.5),
            _num("Ndu", _t(lang, "ndu_label"), c["Ndu"], 2, 15, "", 1, 0.5),
        ], note=_t(lang, "cpt_note")),
    ]


def method_options(param: str, lang: str = "en") -> List[tuple]:
    """The choices of one parameter's select: all combined, or one correlation."""
    options = [("auto", _t(lang, "method_auto"))]
    for method in methods_for(param):
        options.append((method.key, f"{reference(method.key, lang)} · "
                                    f"{_t(lang, 'source_' + method.source)}"))
    return options


#: Parameters that have a correlation to choose: more than one way to get them
CHOOSABLE = [p for p in PARAMS if len(methods_for(p)) > 1]


def option_groups(lang: str = "en") -> List[Group]:
    o = DEFAULT_CONFIG["options"]
    return [
        Group(_t(lang, "group_options"), [
            _select("combine", _t(lang, "combine_label"), o["combine"],
                    _choices(lang, "combine", COMBINE)),
            _num("Eu_ratio", _t(lang, "eu_ratio_label"), o["Eu_ratio"], 50, 2000, "", 0, 25),
            _num("nu_granular", _t(lang, "nu_granular_label"), o["nu_granular"], 0, 0.5, "",
                 2, 0.01),
            _num("nu_cohesive", _t(lang, "nu_cohesive_label"), o["nu_cohesive"], 0, 0.5, "",
                 2, 0.01),
        ], note=_t(lang, "options_note")),
        Group(_t(lang, "group_methods"), [
            _select(f"method_{p}", _t(lang, f"param_{p}"), "auto", method_options(p, lang))
            for p in CHOOSABLE
        ]),
    ]


# --------------------------------------------------------------------------- #
#  Tables: soil layers and the three kinds of test
# --------------------------------------------------------------------------- #

SOIL_NUMBERS = ["thickness", "gravel", "fines", "LL", "PL", "w", "Gs", "gamma", "gamma_sat",
                "e0", "D10", "qu"]

#: The numeric columns of each test table
TEST_COLUMNS = {
    "spt_tests": ["depth", "N"],
    "cpt_tests": ["depth", "qc", "fs", "u2"],
    "vs_tests": ["depth", "Vs"],
}


def soil_columns(lang: str = "en") -> List[dict]:
    """Columns of the soil profile table."""
    def number(key):
        return {"key": key, "label": _t(lang, f"col_{key}"), "kind": "number"}

    return ([{"key": "name", "label": _t(lang, "col_name"), "kind": "text"},
             number("thickness"),
             {"key": "behaviour", "label": _t(lang, "col_behaviour"), "kind": "select",
              "options": [{"value": v, "label": _t(lang, f"behaviour_{v}")} for v in BEHAVIOURS]}]
            + [number(key) for key in SOIL_NUMBERS[1:]])


def test_columns(table: str, lang: str = "en") -> List[dict]:
    return [{"key": key, "label": _t(lang, f"col_{key}"), "kind": "number"}
            for key in TEST_COLUMNS[table]]


def default_rows(table: str) -> List[dict]:
    return [dict(row) for row in DEFAULT_CONFIG[table]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "tests": {"groups": [g.to_dict() for g in test_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "soil": {"columns": soil_columns(lang), "rows": default_rows("soil_profile"),
                 "note": _t(lang, "soil_note")},
        "spt": {"columns": test_columns("spt_tests", lang)},
        "cpt": {"columns": test_columns("cpt_tests", lang)},
        "vs": {"columns": test_columns("vs_tests", lang)},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return project_groups(lang) + test_groups(lang) + option_groups(lang)


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    for table in TABLES:
        values[table] = default_rows(table)
    return values


# --------------------------------------------------------------------------- #
#  Readers: flat values <-> configuration dictionary
# --------------------------------------------------------------------------- #

def _f(values: dict, key: str, default: float = 0.0) -> float:
    """A numeric field; missing or empty falls back to the default."""
    v = values.get(key, default)
    if v is None or v == "":
        return float(default)
    return float(v)


def _s(values: dict, key: str, default: str = "", allowed: Optional[List[str]] = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def read_soil_profile(values: dict) -> List[dict]:
    """Soil layers from the table; rows without a usable thickness are dropped."""
    layers = []
    for row in values.get("soil_profile") or []:
        try:
            thickness = float(row.get("thickness"))
        except (TypeError, ValueError):
            continue
        if thickness <= 0:
            continue
        layer = {"name": str(row.get("name") or "").strip() or "Layer",
                 "behaviour": _s(row, "behaviour", "granular", BEHAVIOURS)}
        for key in SOIL_NUMBERS:
            try:
                layer[key] = _f(row, key, 0.0)
            except (TypeError, ValueError):
                layer[key] = 0.0
        layer["thickness"] = thickness
        layers.append(layer)
    return layers


def read_tests(values: dict, table: str) -> List[dict]:
    """The rows of a test table; rows with a missing or unreadable number are dropped."""
    rows = []
    for row in values.get(table) or []:
        try:
            clean = {key: float(row.get(key)) for key in TEST_COLUMNS[table]
                     if key != "u2"}
            if "u2" in TEST_COLUMNS[table]:
                u2 = row.get("u2")
                clean["u2"] = float(u2) if u2 not in (None, "") else 0.0
        except (TypeError, ValueError):
            continue
        rows.append(clean)
    return rows


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    d = DEFAULT_CONFIG
    cfg["project_info"] = {"title": _s(values, "title", d["project_info"]["title"]),
                           "analyst": str(values.get("analyst") or "")}
    cfg["groundwater"] = {"depth": _f(values, "water_depth", d["groundwater"]["depth"]),
                          "gamma_water": _f(values, "gamma_water",
                                            d["groundwater"]["gamma_water"])}
    s = d["spt"]
    cfg["spt"] = {
        "energy_ratio": _f(values, "er", s["energy_ratio"]),
        "borehole": _f(values, "borehole", s["borehole"]),
        "sampler": _s(values, "sampler", s["sampler"], SAMPLERS),
        "stickup": _f(values, "stickup", s["stickup"]),
        "cn_method": _s(values, "cn_method", s["cn_method"], CN_METHODS),
        "cn_max": _f(values, "cn_max", s["cn_max"]),
    }
    c = d["cpt"]
    cfg["cpt"] = {key: _f(values, key, c[key]) for key in ("area_ratio", "Nkt", "Ndu")}
    o = d["options"]
    methods = {}
    for param in CHOOSABLE:
        allowed = ["auto"] + [m.key for m in methods_for(param)]
        choice = _s(values, f"method_{param}", "auto", allowed)
        if choice != "auto":
            methods[param] = choice
    cfg["options"] = {
        "combine": _s(values, "combine", o["combine"], COMBINE),
        "Eu_ratio": _f(values, "Eu_ratio", o["Eu_ratio"]),
        "nu_granular": _f(values, "nu_granular", o["nu_granular"]),
        "nu_cohesive": _f(values, "nu_cohesive", o["nu_cohesive"]),
        "methods": methods,
    }
    cfg["soil_profile"] = read_soil_profile(values)
    for table in TABLES[1:]:
        cfg[table] = read_tests(values, table)
    return cfg


#: Flat key <- (section, key) of the configuration
_MAP = [("title", "project_info", "title"), ("analyst", "project_info", "analyst"),
        ("water_depth", "groundwater", "depth"), ("gamma_water", "groundwater", "gamma_water"),
        ("er", "spt", "energy_ratio"), ("borehole", "spt", "borehole"),
        ("sampler", "spt", "sampler"), ("stickup", "spt", "stickup"),
        ("cn_method", "spt", "cn_method"), ("cn_max", "spt", "cn_max")] + \
    [(k, "cpt", k) for k in ("area_ratio", "Nkt", "Ndu")] + \
    [(k, "options", k) for k in ("combine", "Eu_ratio", "nu_granular", "nu_cohesive")]


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.correlation` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, section, key in _MAP:
        if key in (cfg.get(section) or {}):
            values[flat] = cfg[section][key]
    chosen = (cfg.get("options") or {}).get("methods") or {}
    for param in CHOOSABLE:
        values[f"method_{param}"] = chosen.get(param, "auto")
    if cfg.get("soil_profile"):
        blank = {key: 0.0 for key in SOIL_NUMBERS}
        values["soil_profile"] = [{"name": "Layer", "behaviour": "granular", **blank, **layer}
                                  for layer in cfg["soil_profile"] if isinstance(layer, dict)]
    for table in TABLES[1:]:
        if table in cfg:
            values[table] = [dict(row) for row in cfg[table] or [] if isinstance(row, dict)]
    return values


def project_file(values: dict) -> Dict[str, Any]:
    """What `Save` writes: the configuration."""
    return {"format": FILE_FORMAT, "version": FILE_VERSION, **to_config(values)}
