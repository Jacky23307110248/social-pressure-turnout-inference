from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTE_DIR = ROOT / "technical_note"
SOURCE = NOTE_DIR / "technical_note.tex"
LOCAL_PDF = NOTE_DIR / "technical_note.pdf"
LOG = NOTE_DIR / "technical_note.log"
FINAL_PDF = ROOT / "output" / "pdf" / "social_pressure_technical_note.pdf"

VERIFIED_HASHES = {
    ROOT / "results" / "primary_analysis.json": "9A556EC45F0E8A823A54C02D67D87F85F5072FB7F014B634A74DE25FBADDC2B7",
    ROOT / "results" / "robustness_analysis.json": "B2DFECB7F4E0CD5705600235697AA908451F079AA360448DB6511CDFEE18FB5D",
    ROOT / "results" / "secondary_analysis.json": "D23EF6C4015D372E87B232DBE978C2B236F9FC7CDE67D496B36B772EB5024089",
}

REQUIRED_FIGURES = tuple(
    ROOT / "output" / "pdf" / name
    for name in (
        "figure_1_pressure_gradient.pdf",
        "figure_2_prior_vote_heterogeneity.pdf",
        "figure_3_robustness_forest.pdf",
        "figure_4_design_interference.pdf",
    )
)

REQUIRED_SOURCE_STRINGS = (
    "344,084",
    "180,002",
    "8.131",
    "7.263",
    "8.999",
    "household-assignment policy",
    "not identified",
    "figure_1_pressure_gradient",
    "figure_2_prior_vote_heterogeneity",
    "figure_3_robustness_forest",
    "figure_4_design_interference",
)

PROHIBITED_SOURCE_PATTERNS = {
    "bullet environment": r"\\begin\{(?:itemize|enumerate|description)\}",
    "double quotation mark": r'"',
    "synthetic data claim": r"synthetic voters|simulated outcomes were used",
    "pure direct-effect overclaim": r"pure (?:individual|psychological) direct effect (?:is|was) identified",
    "spillover overclaim": r"(?:no|zero) spillover effect",
    "publication overclaim": r"\bwe prove\b|\bnew experiment\b|\boriginal discovery\b",
}

PROHIBITED_LOG_PATTERNS = (
    "Overfull",
    "Underfull",
    "undefined references",
    "undefined citations",
    "LaTeX Font Warning",
    "Missing character",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def audit_verified_inputs() -> None:
    failures = [str(path.relative_to(ROOT)) for path, expected in VERIFIED_HASHES.items() if sha256(path) != expected]
    if failures:
        raise RuntimeError("Verified input hash audit failed: " + ", ".join(failures))
    missing_figures = [str(path.relative_to(ROOT)) for path in REQUIRED_FIGURES if not path.is_file() or path.stat().st_size == 0]
    if missing_figures:
        raise RuntimeError("Required figure audit failed: " + ", ".join(missing_figures))

    primary = json.loads((ROOT / "results" / "primary_analysis.json").read_text(encoding="utf-8"))
    post = json.loads((ROOT / "results" / "robustness_analysis.json").read_text(encoding="utf-8"))
    mechanism = json.loads((ROOT / "results" / "secondary_analysis.json").read_text(encoding="utf-8"))
    checks = {
        "primary effect": (primary["primary_neighbors_vs_control"]["effect"], 0.08130991292051308),
        "primary cluster SE": (primary["primary_neighbors_vs_control"]["cluster_se"], 0.00336954742107693),
        "adjusted effect": (primary["adjusted_block_fixed_effect"]["effect"], 0.08146466874413921),
        "household effect": (primary["household_level_replication"]["effect"], 0.08478807597718736),
        "randomization p": (primary["block_stratified_randomization_inference"]["two_sided_p"], 0.001),
        "99 percent lower": (post["primary_99pct_confidence_interval"]["lower"], 0.07263039587473481),
        "99 percent upper": (post["primary_99pct_confidence_interval"]["upper"], 0.08998942996629135),
        "duplicate effect": (post["exact_duplicate_sensitivity"]["effect"], 0.08125326511276969),
        "prior interaction": (mechanism["heterogeneity"]["interactions"][0]["effect"], 0.031915045886225735),
        "prior interaction Holm p": (mechanism["heterogeneity"]["interactions"][0]["holm_adjusted_p"], 4.574770257795765e-08),
    }
    bad = [name for name, (observed, expected) in checks.items() if abs(observed - expected) > 1e-15]
    if bad:
        raise RuntimeError("Verified statistic audit failed: " + ", ".join(bad))


def audit_source() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    missing = [value for value in REQUIRED_SOURCE_STRINGS if value not in text]
    if missing:
        raise RuntimeError("Technical Note is missing required content: " + ", ".join(missing))
    failures = [
        name
        for name, pattern in PROHIBITED_SOURCE_PATTERNS.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
    if failures:
        raise RuntimeError("Technical Note source audit failed: " + ", ".join(failures))


def compile_note() -> None:
    executable = shutil.which("xelatex")
    if executable is None:
        raise RuntimeError("xelatex is required to compile the Technical Note")
    command = (executable, "-interaction=nonstopmode", "-halt-on-error", SOURCE.name)
    for _ in range(2):
        subprocess.run(command, cwd=NOTE_DIR, check=True)


def audit_log() -> None:
    text = LOG.read_text(encoding="utf-8", errors="replace")
    failures = [pattern for pattern in PROHIBITED_LOG_PATTERNS if pattern in text]
    if failures:
        raise RuntimeError("Technical Note layout audit failed: " + ", ".join(failures))


def main() -> None:
    audit_verified_inputs()
    audit_source()
    compile_note()
    audit_log()
    FINAL_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LOCAL_PDF, FINAL_PDF)
    print(f"Technical Note written to {FINAL_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
