"""
SlipSurface IQ Correlation — soil parameters from laboratory and field tests, driven from a browser.

The program turns the results of a site investigation into the parameters a
design needs, layer by layer, using the correlations of the literature:

    1. Index           — PI, LI, phase relations (e0, γ, γsat), USCS group
    2. Stresses        — σv0, u0 and σ'v0 at every test depth
    3. Field tests     — SPT corrected to N60 and (N1)60; CPT(u) normalised to
                         Qtn, Fr, Bq and the soil behaviour type index Ic
                         (Robertson 2009); measured shear wave velocities
    4. Correlations    — every parameter from every correlation that applies:
                         Dr, φ', cu, σ'p, OCR, K0, E, Eu, M, Cc, Cr, Cα, cv, Vs,
                         G0 and k
    5. Selection       — one value per layer, from a chosen correlation or
                         combined (mean, median or a cautious estimate), with
                         the spread of the correlations beside it

The parameters can be sent straight on to SlipSurface IQ Settle and SlipSurface IQ Bearing as
their project files.

The interface is a local web server driven from the browser (standard library
only), so the program also runs over a remote session or inside a container,
where a desktop toolkit would need a display it does not have.

Package layout
--------------
    slipsurface.correlation.config        app identity, defaults, themes, palette
    slipsurface.correlation.i18n          every text of the program, English and Turkish
    slipsurface.correlation.lab           index properties, phase relations, USCS
    slipsurface.correlation.insitu        SPT corrections and CPT normalisation
    slipsurface.correlation.correlations  the catalogue of correlations
    slipsurface.correlation.engine        the analysis: stresses, tests, selection
    slipsurface.correlation.exporters     project files for SlipSurface IQ Settle and Bearing
    slipsurface.correlation.plotting      figures
    slipsurface.correlation.report        calculation report: HTML, PDF, DOCX
    slipsurface.correlation.forms         input schema and readers (interface-independent)
    slipsurface.correlation.web           local web server and the browser interface

Run it:  slipsurface-correlation            (or  python -m slipsurface.correlation)
"""

from slipsurface.versioning import module_version

__version__ = module_version(__file__)

APP_NAME = "SlipSurface IQ Correlation"
ORG = "SlipSurface IQ"

__all__ = ["__version__", "APP_NAME", "ORG"]
