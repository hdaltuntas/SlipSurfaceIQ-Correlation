"""
Laboratory results: index properties, phase relations and classification.

    Atterberg limits   PI = LL − PL,  LI = (w − PL)/PI,  Ic = (LL − w)/PI
    Phase relations    e = w·Gs for a saturated soil; γd = Gs·γw/(1 + e),
                       γsat = (Gs + e)·γw/(1 + e), γ = Gs·(1 + w)·γw/(1 + e)
    USCS               the group symbol of ASTM D2487 from the gravel and fines
                       contents and the plasticity of the fines (Casagrande's
                       A-line PI = 0.73·(LL − 20))

Water contents and grain-size fractions are in per cent, as they are reported.
A value of zero means "not measured"; the functions return None for what
cannot be worked out from what was measured.
"""

from __future__ import annotations

from typing import Dict, Optional

__all__ = ["measured", "plasticity", "phase", "uscs", "a_line", "USCS_GROUPS"]


def measured(value) -> Optional[float]:
    """A measured value, or None for a zero / missing one."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def a_line(LL: float) -> float:
    """Casagrande's A-line."""
    return 0.73 * (float(LL) - 20.0)


def plasticity(LL, PL, w=None) -> Dict[str, Optional[float]]:
    """PI, the liquidity index and the consistency index."""
    LL, PL, w = measured(LL), measured(PL), measured(w)
    if LL is None or PL is None or LL <= PL:
        # A non-plastic soil (or limits that were not measured)
        return {"LL": LL, "PL": PL, "PI": None, "LI": None, "IC": None}
    PI = LL - PL
    LI = (w - PL) / PI if w is not None else None
    IC = (LL - w) / PI if w is not None else None
    return {"LL": LL, "PL": PL, "PI": PI, "LI": LI, "IC": IC}


def phase(w, Gs, e0=None, gamma_w: float = 9.81, saturated: bool = True) -> Dict[str, Optional[float]]:
    """Void ratio and unit weights from the water content, Gs and e0.

    A measured e0 is used as it is. Without one, e = w·Gs is taken for a
    saturated soil (`saturated`) — below the water table, or a clay — and
    nothing is estimated otherwise.
    """
    w, Gs, e0 = measured(w), measured(Gs), measured(e0)
    source = "lab" if e0 is not None else None
    if e0 is None and saturated and w is not None and Gs is not None:
        e0, source = w / 100.0 * Gs, "wGs"
    if e0 is None or Gs is None:
        return {"e0": e0, "source": source, "gamma_d": None, "gamma_sat": None, "gamma": None,
                "Sr": None, "n": None}
    gamma_d = Gs * gamma_w / (1.0 + e0)
    gamma_sat = (Gs + e0) * gamma_w / (1.0 + e0)
    Sr = min(w / 100.0 * Gs / e0, 1.0) if w is not None else None
    gamma = gamma_d * (1.0 + w / 100.0) if w is not None and Sr is not None and Sr < 1.0 \
        else gamma_sat
    return {"e0": e0, "source": source, "gamma_d": gamma_d, "gamma_sat": gamma_sat,
            "gamma": gamma, "Sr": Sr, "n": e0 / (1.0 + e0)}


#: The USCS groups the program names
USCS_GROUPS = ["GW", "GP", "GM", "GC", "SW", "SP", "SM", "SC", "ML", "CL", "CL-ML", "MH", "CH"]


def _fines_type(LL: Optional[float], PI: Optional[float]) -> Optional[str]:
    """M or C (or CL-ML) from where the fines plot on the plasticity chart."""
    if LL is None:
        return None
    if PI is None or PI < 4.0 or PI < a_line(LL):
        return "M"
    if PI <= 7.0:
        return "CL-ML"
    return "C"


def uscs(gravel, fines, LL, PL) -> str:
    """The USCS group symbol; a pair when the tests do not settle it.

    Without a grading curve the coefficients Cu and Cc are unknown, so a clean
    sand or gravel is given as "SW/SP"; without Atterberg limits the fines are
    "M/C".
    """
    gravel = measured(gravel) or 0.0
    fines = measured(fines)
    info = plasticity(LL, PL)
    kind = _fines_type(info["LL"], info["PI"])
    if fines is None:
        return "—"

    if fines >= 50.0:                                  # fine-grained
        if kind is None:
            return "ML/CL"
        if kind == "CL-ML":
            return "CL-ML"
        high = info["LL"] >= 50.0
        return ("M" if kind == "M" else "C") + ("H" if high else "L")

    sand = max(100.0 - gravel - fines, 0.0)
    main = "G" if gravel > sand else "S"
    fine_letter = {"M": "M", "C": "C", "CL-ML": "C"}.get(kind) if kind else None
    if fines < 5.0:
        return f"{main}W/{main}P"
    if fines <= 12.0:
        suffix = fine_letter or "M"
        return f"{main}W-{main}{suffix}/{main}P-{main}{suffix}"
    if fine_letter is None:
        return f"{main}M/{main}C"
    if kind == "CL-ML":
        return f"{main}C-{main}M"
    return main + fine_letter
