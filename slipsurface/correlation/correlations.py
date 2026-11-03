"""
The catalogue of correlations.

Every correlation the program knows is declared once, in `METHODS`: the
parameter it gives, the test it reads, the soils it was written for, its
formula and its source. The functions below evaluate them — one SPT blow
count, one CPT reading or one layer's laboratory results at a time — and
return ``{method key: value}``; the engine averages them over a layer and
chooses or combines one value per parameter.

Units: stresses and pressures in kPa, qc in MPa, moduli in MPa, Vs in m/s,
k in m/s, cv in m²/year, Dr in per cent, angles in degrees.

The references are listed in full in docs/theory.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional

from .config import PA

__all__ = ["Method", "METHODS", "methods_for", "reference", "spt_point", "cpt_point", "lab_layer",
           "stroud_f1", "SECONDS_PER_YEAR"]

SECONDS_PER_YEAR = 365.25 * 24 * 3600.0

#: One tonne-force per square metre, the stress unit of Jamiolkowski et al. (1985) [kPa]
T_PER_M2 = 9.80665


@dataclass(frozen=True)
class Method:
    """One correlation: what it gives, from what, for which soils, and its source."""
    key: str
    param: str
    source: str            # spt | cpt | lab | vs | derived
    behaviour: str         # granular | cohesive | all
    ref: str               # author (year), as it is cited; "@key" names a translated text
    formula: str

    def applies(self, behaviour: str) -> bool:
        return self.behaviour in ("all", behaviour)


_LIST = [
    # ---------------------------------------------------------------- unit weight, e0
    Method("gamma_phase", "gamma", "lab", "all", "@ref_phase",
           "γ = Gs·(1 + w)·γw / (1 + e0)"),
    Method("gamma_rc2010", "gamma", "cpt", "all", "Robertson & Cabal (2010)",
           "γ/γw = 0.27·log Rf + 0.36·log(qt/pa) + 1.236"),
    Method("gsat_phase", "gamma_sat", "lab", "all", "@ref_phase",
           "γsat = (Gs + e0)·γw / (1 + e0)"),
    Method("gsat_rc2010", "gamma_sat", "cpt", "all", "Robertson & Cabal (2010)",
           "γ/γw = 0.27·log Rf + 0.36·log(qt/pa) + 1.236"),
    Method("e0_lab", "e0", "lab", "all", "@ref_lab", "e0"),
    Method("e0_wgs", "e0", "lab", "all", "@ref_phase_sat", "e0 = w·Gs"),
    # ---------------------------------------------------------------- relative density
    Method("dr_skempton1986", "Dr", "spt", "granular", "Skempton (1986)",
           "Dr = √[(N1)60 / 60]"),
    Method("dr_idriss2008", "Dr", "spt", "granular", "Idriss & Boulanger (2008)",
           "Dr = √[(N1)60 / 46]"),
    Method("dr_meyerhof1957", "Dr", "spt", "granular", "Meyerhof (1957)",
           "Dr = 21·√[N60 / (σ'v0/98.1 + 0.7)]"),
    Method("dr_jamiolkowski1985", "Dr", "cpt", "granular", "Jamiolkowski et al. (1985)",
           "Dr = −98 + 66·log[qc / √σ'v0]  (t/m²)"),
    Method("dr_baldi1986", "Dr", "cpt", "granular", "Baldi et al. (1986)",
           "Dr = ln[qc / (157·σ'v0^0.55)] / 2.41  (kPa)"),
    Method("dr_km1990", "Dr", "cpt", "granular", "Kulhawy & Mayne (1990)",
           "Dr = √(qt1 / 305),  qt1 = (qt/pa)/√(σ'v0/pa)"),
    # ---------------------------------------------------------------- friction angle
    Method("phi_wolff1989", "phi", "spt", "granular", "Wolff (1989)",
           "φ' = 27.1 + 0.3·N60 − 0.00054·N60²"),
    Method("phi_hatanaka1996", "phi", "spt", "granular", "Hatanaka & Uchida (1996)",
           "φ' = √[20·(N1)60] + 20"),
    Method("phi_schmertmann1975", "phi", "spt", "granular",
           "Schmertmann (1975); Kulhawy & Mayne (1990)",
           "φ' = arctan[N60 / (12.2 + 20.3·σ'v0/pa)]^0.34"),
    Method("phi_rc1983", "phi", "cpt", "granular", "Robertson & Campanella (1983)",
           "φ' = arctan[0.1 + 0.38·log(qt/σ'v0)]"),
    Method("phi_km1990", "phi", "cpt", "granular", "Kulhawy & Mayne (1990)",
           "φ' = 17.6 + 11·log qt1"),
    Method("phi_kenney1959", "phi", "lab", "cohesive",
           "Kenney (1959); Terzaghi, Peck & Mesri (1996)", "sin φ' = 0.8 − 0.094·ln PI"),
    Method("phi_sorensen2013", "phi", "lab", "cohesive", "Sorensen & Okkels (2013)",
           "φ' = 43 − 10·log PI"),
    # ---------------------------------------------------------------- undrained strength
    Method("cu_stroud1974", "cu", "spt", "cohesive", "Stroud (1974)",
           "cu = f1(PI)·N60,  f1 = 4.2 … 6.5 kPa"),
    Method("cu_hara1974", "cu", "spt", "cohesive", "Hara et al. (1974)", "cu = 29·N60^0.72"),
    Method("cu_terzaghi1967", "cu", "spt", "cohesive", "Terzaghi & Peck (1967)",
           "cu = qu/2 = 6.25·N60"),
    Method("cu_sivrikaya2006", "cu", "spt", "cohesive", "Sivrikaya & Toğrol (2006)",
           "cu = 4.32·N60"),
    Method("cu_nkt", "cu", "cpt", "cohesive", "Lunne et al. (1997); Robertson (2009)",
           "cu = (qt − σv0) / Nkt"),
    Method("cu_ndu", "cu", "cpt", "cohesive", "Lunne et al. (1997)", "cu = (u2 − u0) / NΔu"),
    Method("cu_qu", "cu", "lab", "cohesive", "@ref_qu", "cu = qu / 2"),
    Method("cu_mesri1975", "cu", "derived", "cohesive", "Mesri (1975)", "cu = 0.22·σ'p"),
    # ---------------------------------------------------------------- stress history
    Method("sp_mayne2002", "sigma_p", "spt", "cohesive", "Mayne et al. (2002)",
           "σ'p = 0.47·N60^m·pa  (m = 1 clays, 0.9 silts)"),
    Method("sp_km1990", "sigma_p", "cpt", "cohesive", "Kulhawy & Mayne (1990)",
           "σ'p = 0.33·(qt − σv0)"),
    Method("sp_stas1984", "sigma_p", "lab", "cohesive", "Stas & Kulhawy (1984)",
           "σ'p = pa·10^(1.11 − 1.62·LI)"),
    Method("ocr_sp", "OCR", "derived", "cohesive", "@ref_definition", "OCR = σ'p / σ'v0"),
    Method("ocr_nc", "OCR", "derived", "granular", "@ref_nc",
           "OCR = 1"),
    Method("k0_mayne1982", "K0", "derived", "all", "Jaky (1944); Mayne & Kulhawy (1982)",
           "K0 = (1 − sin φ')·OCR^sin φ'"),
    # ---------------------------------------------------------------- stiffness
    Method("e_km1990", "E", "spt", "granular", "Kulhawy & Mayne (1990)",
           "E = α·pa·N60,  α = 10 (FC ≤ 12 %), 5 (FC > 12 %)"),
    Method("e_bowles1996", "E", "spt", "granular", "Bowles (1996)", "E = 500·(N60 + 15) kPa"),
    Method("e_schmertmann1978", "E", "cpt", "granular", "Schmertmann et al. (1978)",
           "E = 2.5·qc"),
    Method("e_robertson2009", "E", "cpt", "granular", "Robertson (2009)",
           "E = 0.015·10^(0.55·Ic + 1.68)·(qt − σv0)"),
    Method("eu_ratio", "Eu", "derived", "cohesive", "Duncan & Buchignani (1976)",
           "Eu = (Eu/cu)·cu"),
    Method("m_robertson2009", "M", "cpt", "all", "Robertson (2009)",
           "M = αM·(qt − σv0),  αM = Qt ≤ 14 (Ic > 2.2), 0.0188·10^(0.55·Ic + 1.68)"),
    # ---------------------------------------------------------------- compressibility
    Method("cc_skempton1944", "Cc", "lab", "cohesive", "Skempton (1944)",
           "Cc = 0.009·(LL − 10)"),
    Method("cc_azzouz1976", "Cc", "lab", "cohesive", "Azzouz et al. (1976)",
           "Cc = 0.40·(e0 − 0.25)"),
    Method("cc_nishida1956", "Cc", "lab", "cohesive", "Nishida (1956)", "Cc = 1.15·(e0 − 0.35)"),
    Method("cc_koppula1981", "Cc", "lab", "cohesive", "Koppula (1981)", "Cc = 0.01·w"),
    Method("cc_wroth1978", "Cc", "lab", "cohesive", "Wroth & Wood (1978)",
           "Cc = 0.5·Gs·PI/100"),
    Method("cr_nagaraj1985", "Cr", "lab", "cohesive", "Nagaraj & Murty (1985)",
           "Cr = 0.0463·(LL/100)·Gs"),
    Method("cr_ratio", "Cr", "derived", "cohesive", "Kulhawy & Mayne (1990)",
           "Cr = 0.15·Cc  (Cr/Cc ≈ 0.1 … 0.2)"),
    Method("ca_mesri1977", "Calpha", "derived", "cohesive", "Mesri & Godlewski (1977)",
           "Cα = 0.04·Cc"),
    Method("ca_mesri1973", "Calpha", "lab", "cohesive", "Mesri (1973)", "Cα = 0.0001·w"),
    Method("cv_km", "cv", "cpt", "cohesive", "@ref_cv",
           "cv = k·M / γw"),
    # ---------------------------------------------------------------- shear wave velocity
    Method("vs_imai1982", "Vs", "spt", "all", "Imai & Tonouchi (1982)", "Vs = 97·N60^0.314"),
    Method("vs_ohta1978", "Vs", "spt", "all", "Ohta & Goto (1978)", "Vs = 85.35·N60^0.348"),
    Method("vs_iyisan1996", "Vs", "spt", "all", "İyisan (1996)", "Vs = 51.5·N60^0.516"),
    Method("vs_robertson2009", "Vs", "cpt", "all", "Robertson (2009)",
           "Vs = [αvs·(qt − σv0)/pa]^0.5,  αvs = 10^(0.55·Ic + 1.68)"),
    Method("vs_mayne2006", "Vs", "cpt", "all", "Mayne (2006)", "Vs = 118.8·log fs + 18.5"),
    Method("vs_measured", "Vs", "vs", "all", "@ref_measured", "Vs"),
    Method("g0_vs", "G0", "derived", "all", "@ref_elastic", "G0 = (γ/g)·Vs²"),
    # ---------------------------------------------------------------- permeability
    Method("k_hazen1911", "k", "lab", "granular", "Hazen (1911)", "k = 0.01·D10²  (D10 in mm)"),
    Method("k_robertson2010", "k", "cpt", "all", "Robertson (2010)",
           "k = 10^(0.952 − 3.04·Ic) (Ic ≤ 3.27), 10^(−4.52 − 1.37·Ic) (Ic < 4)"),
]

METHODS: Dict[str, Method] = {method.key: method for method in _LIST}


def reference(key: str, lang: str = "en") -> str:
    """How a correlation is cited: author (year), or a description in the language."""
    ref = METHODS[key].ref
    if ref.startswith("@"):
        from .i18n import t
        return t(lang, ref[1:])
    return ref


def methods_for(param: str, behaviour: Optional[str] = None) -> list:
    """The correlations of one parameter (for one soil behaviour, if given)."""
    return [m for m in _LIST if m.param == param
            and (behaviour is None or m.applies(behaviour))]


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _clip(value: Optional[float], lo: float = -math.inf, hi: float = math.inf):
    if value is None or not math.isfinite(value):
        return None
    return min(max(value, lo), hi)


#: Stroud's (1974) f1 = cu/N60 against PI, read from his chart
_STROUD = [(15.0, 6.5), (20.0, 5.5), (25.0, 4.9), (30.0, 4.6), (40.0, 4.4), (60.0, 4.2)]


def stroud_f1(PI: Optional[float]) -> float:
    """Stroud's f1 [kPa]; 4.4 kPa, his value for most clays, when PI is unknown."""
    if PI is None:
        return 4.4
    if PI <= _STROUD[0][0]:
        return _STROUD[0][1]
    for (x0, y0), (x1, y1) in zip(_STROUD, _STROUD[1:]):
        if PI <= x1:
            return y0 + (y1 - y0) * (PI - x0) / (x1 - x0)
    return _STROUD[-1][1]


def _alpha(Ic: float) -> float:
    """10^(0.55·Ic + 1.68), the factor Robertson's (2009) moduli share."""
    return 10.0 ** (0.55 * Ic + 1.68)


# --------------------------------------------------------------------------- #
#  One SPT blow count
# --------------------------------------------------------------------------- #

def spt_point(row: dict, layer: dict) -> Dict[str, float]:
    """The correlations of one corrected blow count, for the layer it was driven in.

    `row` carries N60, N1_60 and the stresses; `layer` the soil behaviour, the
    fines content, PI and the USCS group.
    """
    out: Dict[str, Optional[float]] = {}
    N60, N160 = max(row["N60"], 0.0), max(row["N1_60"], 0.0)
    se = row["sigma_eff"]
    if N60 <= 0:
        return {}
    if layer["behaviour"] == "granular":
        out["dr_skempton1986"] = _clip(100.0 * math.sqrt(N160 / 60.0), 0, 100)
        out["dr_idriss2008"] = _clip(100.0 * math.sqrt(N160 / 46.0), 0, 100)
        out["dr_meyerhof1957"] = _clip(21.0 * math.sqrt(N60 / (se / 98.1 + 0.7)), 0, 100)
        out["phi_wolff1989"] = 27.1 + 0.3 * N60 - 0.00054 * N60 ** 2
        out["phi_hatanaka1996"] = math.sqrt(20.0 * N160) + 20.0
        out["phi_schmertmann1975"] = math.degrees(math.atan(
            (N60 / (12.2 + 20.3 * se / PA)) ** 0.34))
        alpha = 5.0 if (layer.get("fines") or 0.0) > 12.0 else 10.0
        out["e_km1990"] = alpha * PA * N60 / 1000.0
        out["e_bowles1996"] = 500.0 * (N60 + 15.0) / 1000.0
    else:
        out["cu_stroud1974"] = stroud_f1(layer.get("PI")) * N60
        out["cu_hara1974"] = 29.0 * N60 ** 0.72
        out["cu_terzaghi1967"] = 6.25 * N60
        out["cu_sivrikaya2006"] = 4.32 * N60
        m = 0.9 if str(layer.get("uscs", "")).startswith("M") else 1.0
        out["sp_mayne2002"] = 0.47 * N60 ** m * PA
    out["vs_imai1982"] = 97.0 * N60 ** 0.314
    out["vs_ohta1978"] = 85.35 * N60 ** 0.348
    out["vs_iyisan1996"] = 51.5 * N60 ** 0.516
    return {k: v for k, v in out.items() if v is not None}


# --------------------------------------------------------------------------- #
#  One CPT reading
# --------------------------------------------------------------------------- #

def cpt_permeability(Ic: float) -> Optional[float]:
    """Robertson (2010): the hydraulic conductivity from Ic [m/s]."""
    if Ic <= 3.27:
        return 10.0 ** (0.952 - 3.04 * Ic)
    if Ic < 4.0:
        return 10.0 ** (-4.52 - 1.37 * Ic)
    return None


def cpt_point(row: dict, layer: dict, cpt: dict, gamma_w: float = 9.81) -> Dict[str, float]:
    """The correlations of one normalised CPT reading, for the layer it lies in.

    `row` carries qc [MPa], fs, u2, the stresses and what `insitu.cpt_normalise`
    returned (qt, net, Rf, Qt, Qtn, Ic …).
    """
    out: Dict[str, Optional[float]] = {}
    qt, net, se, Ic = row["qt"], row["net"], row["sigma_eff"], row["Ic"]
    qc_kpa = row["qc"] * 1000.0
    if row["Rf"] > 0:
        gamma = gamma_w * (0.27 * math.log10(row["Rf"]) + 0.36 * math.log10(qt / PA) + 1.236)
        gamma = _clip(gamma, 12.0, 24.0)
        out["gamma_rc2010"] = gamma
        out["gsat_rc2010"] = gamma

    if layer["behaviour"] == "granular":
        qt1 = (qt / PA) / math.sqrt(se / PA)
        if qc_kpa > 0:
            out["dr_jamiolkowski1985"] = _clip(
                -98.0 + 66.0 * math.log10((qc_kpa / T_PER_M2) / math.sqrt(se / T_PER_M2)), 0, 100)
            out["dr_baldi1986"] = _clip(
                100.0 * math.log(qc_kpa / (157.0 * se ** 0.55)) / 2.41, 0, 100)
        out["dr_km1990"] = _clip(100.0 * math.sqrt(qt1 / 305.0), 0, 100)
        if qt / se > 1.0:
            out["phi_rc1983"] = math.degrees(math.atan(0.1 + 0.38 * math.log10(qt / se)))
        if qt1 > 0:
            out["phi_km1990"] = _clip(17.6 + 11.0 * math.log10(qt1), 0.0)
        out["e_schmertmann1978"] = 2.5 * qc_kpa / 1000.0
        out["e_robertson2009"] = 0.015 * _alpha(Ic) * net / 1000.0
    else:
        out["cu_nkt"] = net / float(cpt.get("Nkt", 14.0))
        excess = row["u2"] - row["u0"]
        if row["u2"] and excess > 0:
            out["cu_ndu"] = excess / float(cpt.get("Ndu", 6.0))
        out["sp_km1990"] = 0.33 * net

    alpha_m = (min(row["Qt"], 14.0) if Ic > 2.2 else 0.0188 * _alpha(Ic))
    M = alpha_m * net / 1000.0
    out["m_robertson2009"] = M if M > 0 else None
    out["vs_robertson2009"] = math.sqrt(_alpha(Ic) * net / PA)
    if row["fs"] > 1.0:
        out["vs_mayne2006"] = _clip(118.8 * math.log10(row["fs"]) + 18.5, 0.0)
    k = cpt_permeability(Ic)
    out["k_robertson2010"] = k
    if layer["behaviour"] == "cohesive" and k is not None and M > 0:
        out["cv_km"] = k * M * 1000.0 / gamma_w * SECONDS_PER_YEAR
    return {key: v for key, v in out.items() if v is not None}


# --------------------------------------------------------------------------- #
#  One layer's laboratory results
# --------------------------------------------------------------------------- #

def lab_layer(layer: dict, index: dict, phase: dict) -> Dict[str, float]:
    """The correlations of a layer's index properties.

    `index` is `lab.plasticity()`, `phase` is `lab.phase()`; `layer` carries w,
    Gs, D10 and qu as they were entered (zero: not measured).
    """
    out: Dict[str, Optional[float]] = {}
    w = layer.get("w") or 0.0
    Gs = layer.get("Gs") or 0.0
    PI, LL, LI = index.get("PI"), index.get("LL"), index.get("LI")
    e0 = phase.get("e0")

    if phase.get("gamma") is not None:
        out["gamma_phase"] = phase["gamma"]
        out["gsat_phase"] = phase["gamma_sat"]
    if e0 is not None:
        out["e0_lab" if phase.get("source") == "lab" else "e0_wgs"] = e0

    if layer["behaviour"] == "cohesive":
        if PI is not None and PI > 0:
            s = 0.8 - 0.094 * math.log(PI)
            if -1.0 < s < 1.0:
                out["phi_kenney1959"] = math.degrees(math.asin(s))
            out["phi_sorensen2013"] = 43.0 - 10.0 * math.log10(PI)
        if (layer.get("qu") or 0.0) > 0:
            out["cu_qu"] = layer["qu"] / 2.0
        if LI is not None:
            out["sp_stas1984"] = PA * 10.0 ** (1.11 - 1.62 * LI)
        if LL is not None:
            out["cc_skempton1944"] = _clip(0.009 * (LL - 10.0), 0.0) or None
            if Gs > 0:
                out["cr_nagaraj1985"] = 0.0463 * LL / 100.0 * Gs
        if e0 is not None:
            out["cc_azzouz1976"] = _clip(0.40 * (e0 - 0.25), 0.0) or None
            out["cc_nishida1956"] = _clip(1.15 * (e0 - 0.35), 0.0) or None
        if w > 0:
            out["cc_koppula1981"] = 0.01 * w
            out["ca_mesri1973"] = 0.0001 * w
        if PI is not None and Gs > 0:
            out["cc_wroth1978"] = 0.5 * Gs * PI / 100.0
    elif (layer.get("D10") or 0.0) > 0:
        out["k_hazen1911"] = 0.01 * layer["D10"] ** 2
    return {key: v for key, v in out.items() if v is not None}
