"""
In-situ stresses, and the field tests brought to the form the correlations take.

    Stresses   σv0 = Σ γ·Δz (γ above the water table, γsat below it),
               u0 = γw·(z − zw) below the water table, σ'v0 = σv0 − u0

    SPT        N60 = N·CE·CB·CS·CR (Skempton 1986; Youd et al. 2001)
                   CE = ER/60, CB from the borehole diameter, CS for a sampler
                   without its liners, CR from the rod length
               (N1)60 = CN·N60 with
                   CN = (pa/σ'v0)^0.5                  Liao & Whitman (1986)
                   CN = 2/(1 + σ'v0/pa)                Skempton (1986)
               and CN ≤ CN,max (1.7, Youd et al. 2001)

    CPT(u)     Robertson (2009): qt = qc + u2·(1 − a), Rf = fs/qt,
               Fr = fs/(qt − σv0), Bq = (u2 − u0)/(qt − σv0),
               Qtn = [(qt − σv0)/pa]·(pa/σ'v0)^n,
               Ic = √[(3.47 − log Qtn)² + (log Fr + 1.22)²],
               n = 0.381·Ic + 0.05·σ'v0/pa − 0.15 ≤ 1, found by iteration;
               the soil behaviour type zone (2 … 7) from Ic

Stresses and pressures are in kPa; qc is read in MPa, as it is reported.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from .config import PA

__all__ = ["Profile", "spt_corrections", "rod_factor", "borehole_factor", "cn_factor",
           "cpt_normalise", "sbt_zone", "IC_ZONES"]


class Profile:
    """The in-situ stresses of a layered profile with a water table."""

    def __init__(self, layers: List[dict], zw: float, gamma_w: float = 9.81):
        self.layers = layers            # each with top, bottom, gamma, gamma_sat
        self.zw = float(zw)
        self.gw = float(gamma_w)
        self.depth = layers[-1]["bottom"] if layers else 0.0

    def layer_at(self, z: float) -> Optional[int]:
        """The index of the layer that holds depth z (the last one continues below)."""
        for index, layer in enumerate(self.layers):
            if z < layer["bottom"]:
                return index
        return len(self.layers) - 1 if self.layers else None

    def total_stress(self, z: float) -> float:
        z = max(float(z), 0.0)
        sigma = 0.0
        for index, layer in enumerate(self.layers):
            top = layer["top"]
            # the last layer continues below the profile, for the stresses only
            bottom = layer["bottom"] if index < len(self.layers) - 1 else max(layer["bottom"], z)
            if z <= top:
                break
            lower = min(z, bottom)
            dry = max(min(lower, self.zw) - top, 0.0)
            wet = max(lower - max(top, self.zw), 0.0)
            sigma += dry * layer["gamma"] + wet * layer["gamma_sat"]
        return sigma

    def pore_pressure(self, z: float) -> float:
        return max(float(z) - self.zw, 0.0) * self.gw

    def stresses(self, z: float) -> Dict[str, float]:
        sv = self.total_stress(z)
        u0 = self.pore_pressure(z)
        return {"sigma_v": sv, "u0": u0, "sigma_eff": max(sv - u0, 1e-6)}


# --------------------------------------------------------------------------- #
#  SPT
# --------------------------------------------------------------------------- #

def rod_factor(rod_length: float) -> float:
    """CR of Youd et al. (2001) for the rod length (from the hammer to the sampler)."""
    L = float(rod_length)
    if L < 4.0:
        return 0.75
    if L < 6.0:
        return 0.85
    if L < 10.0:
        return 0.95
    return 1.0


def borehole_factor(diameter_mm: float) -> float:
    """CB of Skempton (1986): 65–115 mm 1.0, 150 mm 1.05, 200 mm 1.15."""
    d = float(diameter_mm)
    if d <= 115.0:
        return 1.0
    if d <= 150.0:
        return 1.05
    return 1.15


def cn_factor(sigma_eff: float, method: str = "liao_whitman", cn_max: float = 1.7) -> float:
    """The overburden correction CN."""
    ratio = max(float(sigma_eff), 1e-6) / PA
    if method == "skempton":
        cn = 2.0 / (1.0 + ratio)
    else:
        cn = ratio ** -0.5
    return min(cn, float(cn_max)) if cn_max and cn_max > 0 else cn


def spt_corrections(N: float, depth: float, sigma_eff: float, spt: dict) -> Dict[str, float]:
    """N60, (N1)60 and the factors that led to them."""
    CE = float(spt.get("energy_ratio", 60.0)) / 60.0
    CB = borehole_factor(spt.get("borehole", 100.0))
    CS = 1.2 if spt.get("sampler") == "no_liner" else 1.0
    CR = rod_factor(float(depth) + float(spt.get("stickup", 0.0)))
    N60 = float(N) * CE * CB * CS * CR
    CN = cn_factor(sigma_eff, spt.get("cn_method", "liao_whitman"), spt.get("cn_max", 1.7))
    return {"CE": CE, "CB": CB, "CS": CS, "CR": CR, "N60": N60, "CN": CN, "N1_60": CN * N60}


# --------------------------------------------------------------------------- #
#  CPT
# --------------------------------------------------------------------------- #

#: Upper Ic of each soil behaviour type zone of Robertson (2009): (zone, Ic below)
IC_ZONES = [(7, 1.31), (6, 2.05), (5, 2.60), (4, 2.95), (3, 3.60), (2, math.inf)]


def sbt_zone(Ic: float) -> int:
    """The soil behaviour type zone (2 … 7) that Ic falls in."""
    for zone, upper in IC_ZONES:
        if Ic < upper:
            return zone
    return 2


def cpt_normalise(qc: float, fs: float, u2: float, stresses: Dict[str, float],
                  area_ratio: float = 0.8) -> Optional[Dict[str, float]]:
    """One CPT reading normalised after Robertson (2009); None if it cannot be.

    `qc` in MPa, `fs` and `u2` in kPa.
    """
    sv, u0, se = stresses["sigma_v"], stresses["u0"], stresses["sigma_eff"]
    qt = float(qc) * 1000.0 + float(u2) * (1.0 - float(area_ratio))
    net = qt - sv
    fs = float(fs)
    if qt <= 0 or net <= 0 or fs <= 0:
        return None
    Fr = fs / net * 100.0
    Rf = fs / qt * 100.0
    Bq = (float(u2) - u0) / net if u2 else 0.0

    n = 1.0
    for _ in range(60):
        Qtn = (net / PA) * (PA / se) ** n
        Ic = math.sqrt((3.47 - math.log10(max(Qtn, 1e-6))) ** 2
                       + (math.log10(Fr) + 1.22) ** 2)
        n_new = min(0.381 * Ic + 0.05 * se / PA - 0.15, 1.0)
        if abs(n_new - n) < 1e-3:
            n = n_new
            break
        n = n_new
    Qtn = (net / PA) * (PA / se) ** n
    Ic = math.sqrt((3.47 - math.log10(max(Qtn, 1e-6))) ** 2 + (math.log10(Fr) + 1.22) ** 2)
    return {"qt": qt, "net": net, "Rf": Rf, "Fr": Fr, "Bq": Bq, "Qt": net / se, "Qtn": Qtn,
            "n": n, "Ic": Ic, "zone": sbt_zone(Ic)}
