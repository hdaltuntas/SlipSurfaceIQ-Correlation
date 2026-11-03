"""
The analysis: from the laboratory and field test results to one set of
parameters per layer.

    1. Index         PI, LI, USCS and the phase relations of every layer
    2. Unit weights  entered, or from the phase relations and the CPT
                     (Robertson & Cabal 2010); a typical value as a last resort
    3. Stresses      σv0, u0 and σ'v0 at every test depth
    4. Tests         each SPT blow count corrected, each CPT reading
                     normalised, and every correlation that applies evaluated
                     at that depth
    5. Layers        each correlation averaged over the tests in the layer
                     (geometrically for k and cv, which span decades); then
                     the derived parameters in the order they need each other:
                     OCR from σ'p, cu after Mesri from σ'p, K0 from φ' and OCR,
                     Eu from cu, Cr and Cα from Cc, G0 from Vs and γ
    6. Selection     one value per parameter: the correlation the user chose,
                     or all of them combined — the median, the mean, or a
                     cautious estimate of the mean (Schneider 1997:
                     Xm ∓ 0.5·s, on the unsafe side of which the parameter
                     errs)

The engine raises `CorrelationError` for input it cannot work with; the key
and parameters of the error are translated by the interface. Warnings are
collected as (key, params) pairs in the same way.
"""

from __future__ import annotations

import copy
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

from . import correlations as corr
from . import insitu, lab
from .config import CAUTIOUS, COMBINE, DEFAULT_CONFIG, PARAMS, G

__all__ = ["CorrelationError", "CorrelationAnalysis", "combine", "TYPICAL_GAMMA"]

#: Typical unit weights (γ, γsat) when nothing better is known [kN/m³]
TYPICAL_GAMMA = {"granular": (18.0, 20.0), "cohesive": (18.0, 18.5)}

#: Parameters averaged geometrically, over the tests in a layer and across correlations
GEOMETRIC = ("k", "cv")

#: Blow count at which the SPT is taken as refusal
REFUSAL = 50


class CorrelationError(ValueError):
    """Input the analysis cannot work with; `key` names the message in i18n."""

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        super().__init__(f"{key} {params}" if params else key)


def _mean(values: List[float], geometric: bool = False) -> float:
    if geometric:
        positive = [v for v in values if v > 0]
        if positive:
            return math.exp(sum(math.log(v) for v in positive) / len(positive))
    return sum(values) / len(values)


def combine(param: str, values: List[float], how: str = "median") -> float:
    """One value from the values of several correlations."""
    if not values:
        return float("nan")
    if len(values) == 1:
        return values[0]
    geometric = param in GEOMETRIC
    if geometric:
        logs = [math.log10(v) for v in values if v > 0]
        if not logs:
            return values[0]
        return 10.0 ** combine("_log", logs, how if how != "cautious" else "median")
    if how == "mean":
        return _mean(values)
    if how == "cautious" and param in CAUTIOUS:
        mean, s = _mean(values), statistics.stdev(values)
        estimate = mean - 0.5 * s if CAUTIOUS[param] == "low" else mean + 0.5 * s
        return min(max(estimate, min(values)), max(values))
    return statistics.median(values)


class CorrelationAnalysis:
    """Soil parameters for every layer of one borehole / sounding."""

    def __init__(self, config: Dict[str, Any]):
        self.config = copy.deepcopy(config)
        d = DEFAULT_CONFIG
        gw = {**d["groundwater"], **(self.config.get("groundwater") or {})}
        self.zw = float(gw["depth"])
        self.gw = float(gw["gamma_water"])
        self.spt = {**d["spt"], **(self.config.get("spt") or {})}
        self.cpt = {**d["cpt"], **(self.config.get("cpt") or {})}
        opts = {**d["options"], **(self.config.get("options") or {})}
        self.combine = opts["combine"] if opts["combine"] in COMBINE else "median"
        self.Eu_ratio = float(opts["Eu_ratio"])
        self.nu = {"granular": float(opts["nu_granular"]),
                   "cohesive": float(opts["nu_cohesive"])}
        self.chosen = {k: v for k, v in (opts.get("methods") or {}).items()
                       if v and v != "auto" and v in corr.METHODS}

        self.layers: List[dict] = []
        top = 0.0
        for row in self.config.get("soil_profile") or []:
            layer = dict(row)
            layer["top"], layer["bottom"] = top, top + float(row["thickness"])
            top = layer["bottom"]
            self.layers.append(layer)
        self.spt_tests = [dict(r) for r in self.config.get("spt_tests") or []]
        self.cpt_tests = [dict(r) for r in self.config.get("cpt_tests") or []]
        self.vs_tests = [dict(r) for r in self.config.get("vs_tests") or []]
        self._validate()
        self.results: Dict[str, Any] = {}
        self.warnings: List[Tuple[str, dict]] = []

    # ------------------------------------------------------------------ checks
    def _validate(self) -> None:
        if not self.layers:
            raise CorrelationError("err_no_layers")
        if self.zw < 0:
            raise CorrelationError("err_water")
        if not 9.0 <= self.gw <= 11.0:
            raise CorrelationError("err_gamma_w")
        if not 0.0 < float(self.cpt["area_ratio"]) <= 1.0:
            raise CorrelationError("err_area_ratio")
        for key, value in (("ER", self.spt["energy_ratio"]), ("Nkt", self.cpt["Nkt"]),
                           ("NΔu", self.cpt["Ndu"]), ("Eu/cu", self.Eu_ratio)):
            if float(value) <= 0:
                raise CorrelationError("err_factor", name=key)
        for layer in self.layers:
            for key in ("gamma", "gamma_sat", "w", "Gs", "e0", "LL", "PL", "fines", "gravel",
                        "D10", "qu"):
                if float(layer.get(key) or 0.0) < 0:
                    raise CorrelationError("err_negative", name=layer["name"], field=key)
            if float(layer.get("fines") or 0) + float(layer.get("gravel") or 0) > 100.0:
                raise CorrelationError("err_fractions", name=layer["name"])
        for nu in self.nu.values():
            if not 0.0 <= nu < 0.5 + 1e-9:
                raise CorrelationError("err_nu")

    def warn(self, key: str, **params) -> None:
        if (key, params) not in self.warnings:
            self.warnings.append((key, params))

    # ------------------------------------------------------------------ selection
    def select(self, param: str, methods: Dict[str, dict], layer_name: str = "",
               quiet: bool = False) -> Tuple[Optional[float], str]:
        """One value of a parameter from its correlations: (value, how it was chosen)."""
        values = {k: m["value"] for k, m in methods.items()
                  if m["value"] is not None and math.isfinite(m["value"])}
        chosen = self.chosen.get(param)
        if chosen:
            if chosen in values:
                return values[chosen], chosen
            if values and not quiet:
                self.warn("warn_method_missing", param=param, name=layer_name,
                          method=chosen)
        if not values:
            return None, ""
        if len(values) == 1:
            key = next(iter(values))
            return values[key], key
        return combine(param, list(values.values()), self.combine), "combined"

    def _row_selection(self, row_methods: Dict[str, float]) -> Dict[str, float]:
        """The value of every parameter at one test depth, for the depth plots."""
        grouped: Dict[str, Dict[str, dict]] = {}
        for key, value in row_methods.items():
            grouped.setdefault(corr.METHODS[key].param, {})[key] = {"value": value, "n": 1}
        out = {}
        for param, methods in grouped.items():
            value, _ = self.select(param, methods, quiet=True)
            if value is not None:
                out[param] = value
        return out

    # ------------------------------------------------------------------ the analysis
    def run(self) -> "CorrelationAnalysis":
        self.warnings = []
        self._index()
        self._unit_weights()
        self.profile = insitu.Profile(self.layers, self.zw, self.gw)
        spt_rows = self._spt()
        cpt_rows = self._cpt()
        vs_rows = self._vs()
        layers = [self._layer(i, spt_rows, cpt_rows, vs_rows) for i in range(len(self.layers))]
        self.results = {
            "layers": layers,
            "spt": spt_rows,
            "cpt": cpt_rows,
            "vs": vs_rows,
            "warnings": list(self.warnings),
            "counts": {
                "layers": len(layers),
                "spt": len(spt_rows),
                "cpt": len(cpt_rows),
                "vs": len(vs_rows),
                "methods": len({k for lay in layers for p in lay["params"].values()
                                for k in p["methods"]}),
                "params": sum(1 for lay in layers for p in lay["params"].values()
                              if p["value"] is not None),
            },
        }
        return self

    # 1 ----------------------------------------------------------------- index
    def _index(self) -> None:
        for layer in self.layers:
            info = lab.plasticity(layer.get("LL"), layer.get("PL"), layer.get("w"))
            layer["PI"], layer["LI"], layer["IC"] = info["PI"], info["LI"], info["IC"]
            layer["uscs"] = lab.uscs(layer.get("gravel"), layer.get("fines"),
                                     layer.get("LL"), layer.get("PL"))
            saturated = layer["behaviour"] == "cohesive" or layer["top"] >= self.zw
            layer["phase"] = lab.phase(layer.get("w"), layer.get("Gs"), layer.get("e0"),
                                       self.gw, saturated)
            layer["lab"] = corr.lab_layer(layer, info, layer["phase"])

    # 2 ----------------------------------------------------------------- unit weights
    def _cpt_gamma(self) -> Dict[int, List[float]]:
        """CPT unit weights per layer; they need qt and Rf only, not the stresses."""
        a = float(self.cpt["area_ratio"])
        out: Dict[int, List[float]] = {}
        for row in self.cpt_tests:
            try:
                z, qc, fs, u2 = (float(row.get(k) or 0.0) for k in ("depth", "qc", "fs", "u2"))
            except (TypeError, ValueError):
                continue
            qt = qc * 1000.0 + u2 * (1.0 - a)
            if qt <= 0 or fs <= 0 or z < 0:
                continue
            rf = fs / qt * 100.0
            gamma = self.gw * (0.27 * math.log10(rf) + 0.36 * math.log10(qt / corr.PA) + 1.236)
            index = self._layer_of(z)
            if index is not None:
                out.setdefault(index, []).append(min(max(gamma, 12.0), 24.0))
        return out

    def _layer_of(self, z: float) -> Optional[int]:
        for index, layer in enumerate(self.layers):
            if layer["top"] <= z < layer["bottom"]:
                return index
        if self.layers and math.isclose(z, self.layers[-1]["bottom"]):
            return len(self.layers) - 1
        return None

    def _unit_weights(self) -> None:
        cpt_gamma = self._cpt_gamma()
        for index, layer in enumerate(self.layers):
            methods_g, methods_s = {}, {}
            if "gamma_phase" in layer["lab"]:
                methods_g["gamma_phase"] = {"value": layer["lab"]["gamma_phase"], "n": 1}
                methods_s["gsat_phase"] = {"value": layer["lab"]["gsat_phase"], "n": 1}
            if cpt_gamma.get(index):
                values = cpt_gamma[index]
                methods_g["gamma_rc2010"] = {"value": _mean(values), "n": len(values)}
                methods_s["gsat_rc2010"] = {"value": _mean(values), "n": len(values)}
            g_in, s_in = float(layer.get("gamma") or 0.0), float(layer.get("gamma_sat") or 0.0)
            g_est, how_g = self.select("gamma", methods_g, layer["name"])
            s_est, how_s = self.select("gamma_sat", methods_s, layer["name"])
            if g_in > 0:
                g, how_g = g_in, "input"
            elif g_est is not None:
                g = g_est
            elif s_in > 0:
                g, how_g = s_in, "input"
            else:
                g, how_g = TYPICAL_GAMMA[layer["behaviour"]][0], "typical"
            if s_in > 0:
                s, how_s = s_in, "input"
            elif s_est is not None:
                s = s_est
            elif g_in > 0:
                s, how_s = g_in, "input"
            else:
                s, how_s = TYPICAL_GAMMA[layer["behaviour"]][1], "typical"
            if "typical" in (how_g, how_s):
                self.warn("warn_gamma_typical", name=layer["name"])
            layer["gamma_used"], layer["gamma_sat_used"] = g, s
            layer["unit_weights"] = {
                "gamma": {"value": g, "how": how_g, "methods": methods_g},
                "gamma_sat": {"value": s, "how": how_s, "methods": methods_s},
            }
            # the profile reads these two keys
            layer["gamma"], layer["gamma_sat"] = g, s

    # 3/4 --------------------------------------------------------------- tests
    def _test_layer(self, z: float, kind: str) -> Optional[int]:
        index = self._layer_of(z) if z >= 0 else None
        if index is None:
            self.warn("warn_test_outside", test=kind.upper(), depth=z)
        return index

    def _spt(self) -> List[dict]:
        rows = []
        for test in sorted(self.spt_tests, key=lambda r: float(r.get("depth") or 0.0)):
            try:
                z, N = float(test.get("depth")), float(test.get("N"))
            except (TypeError, ValueError):
                continue
            if N <= 0:
                continue
            index = self._test_layer(z, "spt")
            if index is None:
                continue
            if N >= REFUSAL:
                self.warn("warn_refusal", depth=z)
            layer = self.layers[index]
            row = {"depth": z, "N": N, "layer": index, **self.profile.stresses(z)}
            row.update(insitu.spt_corrections(N, z, row["sigma_eff"], self.spt))
            row["methods"] = corr.spt_point(row, layer)
            row["selected"] = self._row_selection(row["methods"])
            rows.append(row)
        return rows

    def _cpt(self) -> List[dict]:
        rows, skipped = [], 0
        for test in sorted(self.cpt_tests, key=lambda r: float(r.get("depth") or 0.0)):
            try:
                z, qc, fs = float(test.get("depth")), float(test.get("qc")), float(test.get("fs"))
                u2 = float(test.get("u2") or 0.0)
            except (TypeError, ValueError):
                continue
            index = self._test_layer(z, "cpt")
            if index is None:
                continue
            stresses = self.profile.stresses(z)
            norm = insitu.cpt_normalise(qc, fs, u2, stresses, float(self.cpt["area_ratio"]))
            if norm is None:
                skipped += 1
                continue
            row = {"depth": z, "qc": qc, "fs": fs, "u2": u2, "layer": index, **stresses, **norm}
            row["methods"] = corr.cpt_point(row, self.layers[index], self.cpt, self.gw)
            row["selected"] = self._row_selection(row["methods"])
            rows.append(row)
        if skipped:
            self.warn("warn_cpt_skipped", n=skipped)
        return rows

    def _vs(self) -> List[dict]:
        rows = []
        for test in sorted(self.vs_tests, key=lambda r: float(r.get("depth") or 0.0)):
            try:
                z, vs = float(test.get("depth")), float(test.get("Vs"))
            except (TypeError, ValueError):
                continue
            if vs <= 0:
                continue
            index = self._test_layer(z, "vs")
            if index is not None:
                rows.append({"depth": z, "Vs": vs, "layer": index})
        return rows

    # 5/6 --------------------------------------------------------------- layers
    def _layer(self, index: int, spt_rows, cpt_rows, vs_rows) -> dict:
        layer = self.layers[index]
        name, behaviour = layer["name"], layer["behaviour"]
        mid = 0.5 * (layer["top"] + layer["bottom"])
        stress = self.profile.stresses(mid)

        # every correlation of the layer: the average over its tests, or the lab value
        collected: Dict[str, List[float]] = {}
        for rows in (spt_rows, cpt_rows):
            for row in rows:
                if row["layer"] == index:
                    for key, value in row["methods"].items():
                        collected.setdefault(key, []).append(value)
        measured_vs = [r["Vs"] for r in vs_rows if r["layer"] == index]
        if measured_vs:
            collected["vs_measured"] = measured_vs
        by_param: Dict[str, Dict[str, dict]] = {p: {} for p in PARAMS}
        for key, values in collected.items():
            param = corr.METHODS[key].param
            by_param[param][key] = {"value": _mean(values, param in GEOMETRIC),
                                    "n": len(values)}
        for key, value in layer["lab"].items():
            by_param[corr.METHODS[key].param][key] = {"value": value, "n": 1}

        params: Dict[str, dict] = {}

        def settle(param: str, value=None, how=None) -> Optional[float]:
            methods = by_param[param]
            if how is None:
                value, how = self.select(param, methods, name)
            values = [m["value"] for m in methods.values()]
            params[param] = {
                "value": value, "how": how, "methods": methods,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "cov": (statistics.stdev(values) / abs(_mean(values))
                        if len(values) > 1 and _mean(values) else None),
            }
            return value

        for param in ("gamma", "gamma_sat"):
            info = layer["unit_weights"][param]
            by_param[param] = info["methods"]
            settle(param, info["value"], info["how"])
        settle("e0")

        if behaviour == "granular":
            settle("Dr")
            settle("sigma_p", None, "")
            by_param["OCR"]["ocr_nc"] = {"value": 1.0, "n": 1}
            ocr = settle("OCR")
        else:
            settle("Dr", None, "")
            sp = settle("sigma_p")
            if sp is not None:
                by_param["OCR"]["ocr_sp"] = {"value": sp / stress["sigma_eff"], "n": 1}
                by_param["cu"]["cu_mesri1975"] = {"value": 0.22 * sp, "n": 1}
            ocr = settle("OCR")
            if ocr is not None and ocr < 1.0:
                self.warn("warn_ocr_low", name=name, ocr=ocr)
        cu = settle("cu") if behaviour == "cohesive" else settle("cu", None, "")
        phi = settle("phi")

        if phi is not None:
            s = math.sin(math.radians(phi))
            by_param["K0"]["k0_mayne1982"] = {"value": (1.0 - s) * max(ocr or 1.0, 1.0) ** s,
                                              "n": 1}
        settle("K0")

        if behaviour == "granular":
            settle("E")
            settle("Eu", None, "")
        else:
            settle("E", None, "")
            if cu is not None:
                by_param["Eu"]["eu_ratio"] = {"value": self.Eu_ratio * cu / 1000.0, "n": 1}
            settle("Eu")
        settle("M")

        cc = settle("Cc")
        if cc is not None:
            by_param["Cr"]["cr_ratio"] = {"value": 0.15 * cc, "n": 1}
            by_param["Calpha"]["ca_mesri1977"] = {"value": 0.04 * cc, "n": 1}
        settle("Cr")
        settle("Calpha")
        settle("cv")

        vs = settle("Vs")
        if vs is not None:
            gamma = layer["gamma_sat_used"] if mid >= self.zw else layer["gamma_used"]
            by_param["G0"]["g0_vs"] = {"value": gamma / G * vs ** 2 / 1000.0, "n": 1}
        settle("G0")
        settle("k")

        # A CPT that reads the layer as the other kind of soil is worth a word.
        ics = [r["Ic"] for r in cpt_rows if r["layer"] == index]
        zones = [r["zone"] for r in cpt_rows if r["layer"] == index]
        mean_ic = _mean(ics) if ics else None
        if mean_ic is not None:
            if behaviour == "granular" and mean_ic > 2.95:
                self.warn("warn_ic_clay", name=name, ic=mean_ic)
            elif behaviour == "cohesive" and mean_ic < 2.05:
                self.warn("warn_ic_sand", name=name, ic=mean_ic)
        if not any(p["value"] is not None for key, p in params.items()
                   if key not in ("gamma", "gamma_sat", "OCR", "e0")):
            self.warn("warn_no_data", name=name)

        return {
            "index": index, "name": name, "behaviour": behaviour,
            "top": layer["top"], "bottom": layer["bottom"], "mid": mid,
            "sigma_v": stress["sigma_v"], "u0": stress["u0"], "sigma_eff": stress["sigma_eff"],
            "uscs": layer["uscs"], "PI": layer["PI"], "LI": layer["LI"], "IC": layer["IC"],
            "LL": lab.measured(layer.get("LL")), "PL": lab.measured(layer.get("PL")),
            "w": lab.measured(layer.get("w")), "fines": lab.measured(layer.get("fines")),
            "Ic": mean_ic,
            "zone": statistics.mode(zones) if zones else None,
            "n_spt": sum(1 for r in spt_rows if r["layer"] == index),
            "n_cpt": len(ics),
            "n_vs": len(measured_vs),
            "N60": _mean([r["N60"] for r in spt_rows if r["layer"] == index])
            if any(r["layer"] == index for r in spt_rows) else None,
            "N1_60": _mean([r["N1_60"] for r in spt_rows if r["layer"] == index])
            if any(r["layer"] == index for r in spt_rows) else None,
            "params": params,
        }

    # ------------------------------------------------------------------ helpers for others
    def value(self, index: int, param: str) -> Optional[float]:
        """The selected value of one parameter of one layer."""
        return self.results["layers"][index]["params"][param]["value"]
