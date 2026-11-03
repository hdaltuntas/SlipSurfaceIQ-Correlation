# SlipSurfaceIQ Correlation

**SPT, CPT and laboratory correlations — modern desktop GUI**

Complete standalone program extracted from SlipSurfaceIQ-Suite.

## Quick start (Windows / Linux / macOS)

```bash
# 1. Clone
git clone https://github.com/hdaltuntas/SlipSurfaceIQ-Correlation.git
cd SlipSurfaceIQ-Correlation

# 2. (Recommended) virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install
python -m pip install -r requirements.txt

# 4. Run
python main.py
```

Open the example:
- File → Open → `examples/example.correlation.json`

## Features

- Modern card-based UI with sidebar navigation
- Smooth page-transition animation
- Dark / light mode
- Interactive plots (profile, SPT, CPT, strength, stiffness…)
- SPT, CPT, VS and lab correlations
- English / Turkish
- Project save / load

## Requirements

- Python 3.10+
- PySide6, numpy, scipy, matplotlib, reportlab

## CLI check

```bash
python main.py --check
```

License: see LICENSE.

