"""SlipSurfaceIQ Correlation — modern desktop application.

    python main.py
    python main.py --check
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = {
    "PySide6": "PySide6",
    "numpy": "numpy",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "reportlab": "reportlab",
}
MIN_PYTHON = (3, 10)


def check_environment(verbose: bool = True) -> bool:
    ok = True
    if sys.version_info < MIN_PYTHON:
        print(f"[ERROR] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required.")
        ok = False
    missing = []
    for mod, pip_name in REQUIRED.items():
        try:
            m = importlib.import_module(mod)
            if verbose:
                print(f"  {mod:12s} {getattr(m, '__version__', '?')}")
        except ImportError:
            missing.append(pip_name)
    if missing:
        ok = False
        print("[ERROR] Missing: " + ", ".join(missing))
        print(f"Install: {Path(sys.executable).name} -m pip install -r requirements.txt")
    return ok


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="SlipSurfaceIQ Correlation")
    p.add_argument("--check", action="store_true")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    if args.check:
        return 0 if check_environment() else 1
    if not check_environment(verbose=False):
        return 1
    from slipsurface.ui.app import run
    return run()


if __name__ == "__main__":
    sys.exit(main())
