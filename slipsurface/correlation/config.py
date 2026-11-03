"""
Configuration for SlipSurface IQ Correlation: the default project, the choice lists,
the parameters the program derives, and the theme and plot palette shared by
the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `slipsurface.correlation.i18n`.
"""

import math

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE", "SOIL_FILL",
           "BEHAVIOURS", "SAMPLERS", "CN_METHODS", "COMBINE", "PARAMS", "PARAM_UNITS",
           "CAUTIOUS", "ACCENT", "PA", "G"]

#: Atmospheric pressure, the reference stress of the normalised correlations [kPa]
PA = 101.325

#: Gravity, to turn a unit weight into a density [m/s²]
G = 9.81

# --- Choice lists (the first entry is the default where one is needed) -----
BEHAVIOURS = ["granular", "cohesive"]
SAMPLERS = ["standard", "no_liner"]
CN_METHODS = ["liao_whitman", "skempton"]
COMBINE = ["median", "mean", "cautious"]

#: The parameters the program derives for every layer, in the order it shows them:
#: key -> unit
PARAM_UNITS = {
    "gamma": "kN/m³",
    "gamma_sat": "kN/m³",
    "e0": "",
    "Dr": "%",
    "phi": "°",
    "cu": "kPa",
    "sigma_p": "kPa",
    "OCR": "",
    "K0": "",
    "E": "MPa",
    "Eu": "MPa",
    "M": "MPa",
    "Cc": "",
    "Cr": "",
    "Calpha": "",
    "cv": "m²/yr",
    "Vs": "m/s",
    "G0": "MPa",
    "k": "m/s",
}
PARAMS = list(PARAM_UNITS)

#: The side a cautious estimate takes for each parameter: the lower value of a
#: strength or a stiffness, the higher value of a compressibility. Parameters
#: missing here are combined by the median even in a cautious estimate.
CAUTIOUS = {
    "Dr": "low", "phi": "low", "cu": "low", "sigma_p": "low", "OCR": "low", "E": "low",
    "Eu": "low", "M": "low", "Vs": "low", "G0": "low", "cv": "low",
    "Cc": "high", "Cr": "high", "Calpha": "high",
}

# --- Interface theme (web/static/style.css) and plot palette ---------------
# --- kept together so the figures always match the page they are shown on. -
ACCENT = "#5B7A3A"  # the colour of its group in the suite (foundations)

THEMES = {
    "dark": dict(bg="#262624", panel="#30302E", input_bg="#262624", fg="#F5F4ED",
                 fg_dim="#A6A39A", border="#4A4944", hover="#3A3A37", btn="#3A3A37",
                 muted="#6B6A64", accent="#9BBA78", accent_hover="#AECB8D"),
    "light": dict(bg="#F5F4ED", panel="#FAF9F5", input_bg="#FFFFFF", fg="#141413",
                  fg_dim="#73726C", border="#E3E0D5", hover="#F0EEE6", btn="#F0EEE6",
                  muted="#B7B4AA", accent=ACCENT, accent_hover="#4A6630"),
}
# The report's figures: the light palette on white paper.
THEMES["paper"] = dict(THEMES["light"], bg="#FFFFFF", panel="#FFFFFF")

# Semantic colours: the same quantity is the same colour in every figure. Warm and
# muted, to sit on the paper-coloured page; terracotta marks the selected value.
PLOT_PALETTE = dict(
    spt="#5B8DB8", cpt="#8C6BB1", lab="#5E8C4A", vs="#D9A55B", selected="#C6613F",
    input="#141413", water="#6FA8C7", n_field="#A6A39A", n60="#5B8DB8", n160="#C6613F",
    qt="#8C6BB1", fs="#4E9A8A", u2="#6FA8C7", u0="#73726C", ic="#C6613F", limit="#A26A12",
)

#: Colours that tell the correlations of one parameter apart (cycled)
METHOD_COLOURS = ["#5B8DB8", "#8C6BB1", "#4E9A8A", "#D9A55B", "#5E8C4A", "#B0413E",
                  "#6FA8C7", "#A26A12", "#8A8680"]

# Fill colours of the two soil behaviours in the soil column (theme-dependent,
# since a light sandy tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"granular": "#E3C98F", "cohesive": "#A7B8A0"},
    "dark": {"granular": "#8A7250", "cohesive": "#5E6E58"},
}
SOIL_FILL["paper"] = SOIL_FILL["light"]


def _default_cpt() -> list:
    """A CPTu sounding through the default profile, every half metre.

    It is written out by a rule rather than typed in so that it stays smooth:
    a medium dense sand, a soft to firm clay with excess pore pressure, and a
    dense sand below it. The values are illustrative, not a real record.
    """
    rows = []
    for i in range(1, 40):
        z = 0.5 * i
        wobble = math.sin(1.7 * z)
        u0 = max(z - 2.0, 0.0) * 9.81
        if z < 1.5:                                             # fill
            qc, fs, u2 = 3.0 + 0.6 * wobble, 45.0 + 8 * wobble, 0.0
        elif z < 6.0:                                           # medium dense sand
            qc, fs, u2 = 7.0 + 0.9 * z + 1.2 * wobble, 45.0 + 4.0 * z + 6 * wobble, u0
        elif z < 12.0:                                          # soft to firm clay
            qc = 0.55 + 0.035 * (z - 6.0) + 0.04 * wobble
            fs, u2 = 16.0 + 1.2 * (z - 6.0) + 2 * wobble, u0 + 180.0 + 22.0 * (z - 6.0)
        else:                                                   # dense sand
            qc, fs, u2 = 17.0 + 0.8 * (z - 12.0) + 2 * wobble, 120.0 + 6 * (z - 12.0), u0
        rows.append({"depth": round(z, 2), "qc": round(qc, 2), "fs": round(fs, 1),
                     "u2": round(u2, 1)})
    return rows


DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: Borehole BH-1",
        "analyst": "",
    },
    "groundwater": {
        "depth": 2.0,              # below ground surface [m]
        "gamma_water": 9.81,       # [kN/m³]
    },
    # SPT: the corrections of Skempton (1986) and Youd et al. (2001)
    "spt": {
        "energy_ratio": 60.0,      # hammer energy ratio ER [%]
        "borehole": 100.0,         # borehole diameter [mm]
        "sampler": "standard",     # a standard sampler, or one without its liners
        "stickup": 1.0,            # rod above the ground surface [m]
        "cn_method": "liao_whitman",
        "cn_max": 1.7,
    },
    # CPT(u): the cone's net area ratio and the cone factors of the undrained strength
    "cpt": {
        "area_ratio": 0.80,
        "Nkt": 14.0,
        "Ndu": 6.0,
    },
    "options": {
        "combine": "median",       # how the correlations of one parameter become one value
        "Eu_ratio": 300.0,         # Eu / cu
        "nu_granular": 0.30,       # Poisson's ratio sent on with the drained modulus
        "nu_cohesive": 0.45,
        # A named correlation for a parameter, instead of combining them all
        "methods": {},
    },
    # Layers from the ground surface down, with what the laboratory measured.
    # A zero means "not measured": the program estimates it where it can.
    "soil_profile": [
        {"name": "Fill", "thickness": 1.5, "behaviour": "granular", "gravel": 20.0,
         "fines": 25.0, "LL": 0.0, "PL": 0.0, "w": 12.0, "Gs": 2.65, "gamma": 18.0,
         "gamma_sat": 19.0, "e0": 0.0, "D10": 0.0, "qu": 0.0},
        {"name": "Medium dense sand", "thickness": 4.5, "behaviour": "granular", "gravel": 5.0,
         "fines": 8.0, "LL": 0.0, "PL": 0.0, "w": 18.0, "Gs": 2.65, "gamma": 0.0,
         "gamma_sat": 0.0, "e0": 0.0, "D10": 0.12, "qu": 0.0},
        {"name": "Soft to firm clay", "thickness": 6.0, "behaviour": "cohesive", "gravel": 0.0,
         "fines": 92.0, "LL": 48.0, "PL": 22.0, "w": 36.0, "Gs": 2.70, "gamma": 0.0,
         "gamma_sat": 0.0, "e0": 0.0, "D10": 0.0, "qu": 70.0},
        {"name": "Dense sand", "thickness": 8.0, "behaviour": "granular", "gravel": 10.0,
         "fines": 6.0, "LL": 0.0, "PL": 0.0, "w": 15.0, "Gs": 2.66, "gamma": 0.0,
         "gamma_sat": 0.0, "e0": 0.0, "D10": 0.20, "qu": 0.0},
    ],
    # Field tests: depth below the ground surface [m]
    "spt_tests": [
        {"depth": 1.0, "N": 9}, {"depth": 2.5, "N": 11}, {"depth": 4.0, "N": 14},
        {"depth": 5.5, "N": 17}, {"depth": 7.0, "N": 4}, {"depth": 8.5, "N": 5},
        {"depth": 10.0, "N": 6}, {"depth": 11.5, "N": 7}, {"depth": 13.0, "N": 27},
        {"depth": 14.5, "N": 31}, {"depth": 16.0, "N": 34}, {"depth": 17.5, "N": 38},
        {"depth": 19.0, "N": 42},
    ],
    "cpt_tests": _default_cpt(),        # qc [MPa], fs [kPa], u2 [kPa]
    "vs_tests": [                       # measured shear wave velocity [m/s]
        {"depth": 1.0, "Vs": 170.0}, {"depth": 4.0, "Vs": 215.0}, {"depth": 8.0, "Vs": 150.0},
        {"depth": 11.0, "Vs": 175.0}, {"depth": 15.0, "Vs": 290.0}, {"depth": 19.0, "Vs": 330.0},
    ],
}
