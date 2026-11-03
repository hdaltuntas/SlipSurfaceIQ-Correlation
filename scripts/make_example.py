"""Complete working example project for SlipSurfaceIQ Correlation."""

import json
from pathlib import Path

from slipsurface.correlation.forms import defaults, project_file

if __name__ == "__main__":
    data = project_file(defaults("en"))
    Path("examples").mkdir(exist_ok=True)
    Path("examples/example.correlation.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Wrote examples/example.correlation.json")
