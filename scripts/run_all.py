from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(name: str) -> None:
    subprocess.run([sys.executable, str(SCRIPTS / name)], cwd=ROOT, check=True)


def main() -> None:
    run("run_primary_analysis.py")
    run("run_robustness_analysis.py")
    run("run_secondary_analysis.py")
    run("generate_report_assets.py")
    run("build_report.py")
    subprocess.run([sys.executable, "-m", "pytest"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
