from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PDF_DIR = ROOT / "output" / "pdf"
PNG_DIR = ROOT / "output" / "png"
TABLE_DIR = ROOT / "output" / "tables"

NAVY = "#16324F"
TEAL = "#197278"
AMBER = "#E09F3E"
GRAY = "#66717E"
LIGHT = "#D8E1E8"
RED = "#A23E48"


def load_json(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def ci99(record: dict) -> tuple[float, float]:
    crit = t.ppf(0.995, record["degrees_of_freedom"])
    return record["effect"] - crit * record["cluster_se"], record["effect"] + crit * record["cluster_se"]


def fmt_p(value: float) -> str:
    if value < 0.001:
        return f"{value:.2e}"
    return f"{value:.3f}"


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(PDF_DIR / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(PNG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    def clean(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(map(clean, headers)) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    lines.extend("| " + " | ".join(clean(v) for v in row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def write_table(stem: str, headers: list[str], rows: list[list[str]]) -> None:
    with (TABLE_DIR / f"{stem}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        csv.writer(handle).writerows([headers, *rows])
    (TABLE_DIR / f"{stem}.md").write_text(markdown_table(headers, rows), encoding="utf-8")


def setup() -> None:
    for directory in (PDF_DIR, PNG_DIR, TABLE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.edgecolor": GRAY,
        "axes.linewidth": 0.8,
        "xtick.color": NAVY,
        "ytick.color": NAVY,
        "text.color": NAVY,
        "axes.labelcolor": NAVY,
        "pdf.fonttype": 42,
        "savefig.transparent": False,
    })


def figure_1(primary: dict) -> None:
    labels = ["Civic duty", "Hawthorne", "Self", "Neighbors"]
    keys = ["civic_duty", "hawthorne", "self", "neighbors"]
    records = [primary["pressure_gradient"][key] for key in keys]
    effects = np.array([r["effect"] * 100 for r in records])
    bounds = np.array([[v * 100 for v in ci99(r)] for r in records])
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.axvline(0, color=GRAY, linewidth=1)
    ax.errorbar(effects, y, xerr=np.vstack([effects - bounds[:, 0], bounds[:, 1] - effects]),
                fmt="o", color=NAVY, ecolor=TEAL, capsize=4, markersize=7, linewidth=1.8)
    for x, yy in zip(effects, y):
        ax.text(x + 0.25, yy, f"{x:.2f} pp", va="center", fontweight="bold")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(-0.5, 10.2)
    ax.set_xlabel("Turnout effect relative to control (percentage points)")
    fig.suptitle("Increasing social pressure produces an ordered turnout gradient", x=0.08, y=0.975,
                 ha="left", fontweight="bold", fontsize=12)
    fig.text(0.08, 0.915, "Household-clustered 99% confidence intervals", color=GRAY, ha="left")
    ax.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    save_figure(fig, "figure_1_pressure_gradient")


def figure_2(mechanism: dict) -> None:
    records = mechanism["heterogeneity"]["prior_vote_score_bins"]
    x = np.array([r["prior_vote_score"] for r in records])
    effects = np.array([r["effect"] * 100 for r in records])
    bounds = np.array([[v * 100 for v in ci99(r)] for r in records])
    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    ax.axhline(0, color=GRAY, linewidth=1)
    ax.errorbar(x, effects, yerr=np.vstack([effects - bounds[:, 0], bounds[:, 1] - effects]),
                fmt="o", color=NAVY, ecolor=TEAL, capsize=4, markersize=7, linewidth=1.8)
    ax.plot(x, effects, color=TEAL, linewidth=1.2, alpha=0.7)
    for xx, yy, r in zip(x, effects, records):
        ax.text(xx, -1.35, f"n={r['observations']:,}", ha="center", va="top", fontsize=8, color=GRAY)
        ax.text(xx, yy + 0.5, f"{yy:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xlim(-0.45, 5.45)
    ax.set_ylim(-2.0, 13.0)
    ax.set_xlabel("Prior turnout score (0-5 elections)")
    ax.set_ylabel("Neighbors effect (percentage points)")
    fig.suptitle("Treatment effects vary with prior turnout propensity", x=0.08, y=0.975,
                 ha="left", fontweight="bold", fontsize=12)
    fig.text(0.08, 0.915, "Household-clustered 99% confidence intervals; connected points are descriptive",
             color=GRAY, ha="left")
    ax.grid(axis="y", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    save_figure(fig, "figure_2_prior_vote_heterogeneity")


def figure_3(primary: dict, post: dict) -> None:
    entries = [
        ("Primary voter-level ITT", primary["primary_neighbors_vs_control"]),
        ("Block FE + baselines", primary["adjusted_block_fixed_effect"]),
        ("Household-level outcome", primary["household_level_replication"]),
        ("Exact duplicates removed", post["exact_duplicate_sensitivity"]),
        ("Sex = 0", primary["transport"]["sex_0"]),
        ("Sex = 1", primary["transport"]["sex_1"]),
        ("Prior score 0-2", primary["transport"]["prior_low_0_2"]),
        ("Prior score 3-5", primary["transport"]["prior_high_3_5"]),
        ("Single-voter household", post["household_size_transport"]["single_voter_household"]),
        ("Multi-voter household", post["household_size_transport"]["multi_voter_household"]),
    ]
    labels = [e[0] for e in entries]
    records = [e[1] for e in entries]
    effects = np.array([r["effect"] * 100 for r in records])
    bounds = np.array([[v * 100 for v in ci99(r)] for r in records])
    y = np.arange(len(entries))
    colors = [NAVY] * 4 + [TEAL] * 2 + [AMBER] * 2 + [RED] * 2
    fig, ax = plt.subplots(figsize=(7.4, 6.1))
    ax.axvline(0, color=GRAY, linewidth=1)
    for i in range(len(entries)):
        ax.errorbar(effects[i], y[i], xerr=[[effects[i] - bounds[i, 0]], [bounds[i, 1] - effects[i]]],
                    fmt="o", color=colors[i], ecolor=colors[i], capsize=3, markersize=6, linewidth=1.6)
        ax.text(bounds[i, 1] + 0.22, y[i], f"{effects[i]:.2f}", va="center", fontsize=8)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 12.7)
    ax.set_xlabel("Neighbors effect (percentage points)")
    fig.suptitle("The main effect is stable across estimators and observed subgroups", x=0.05, y=0.98,
                 ha="left", fontweight="bold", fontsize=12)
    fig.text(0.05, 0.935, "99% confidence intervals; subgroup contrasts require separate interaction tests",
             color=GRAY, ha="left")
    ax.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    save_figure(fig, "figure_3_robustness_forest")


def figure_4(mechanism: dict) -> None:
    pattern = mechanism["interference_saturation"]["allocation_patterns"][0]
    labels = ["Control", "Hawthorne", "Civic duty", "Neighbors", "Self"]
    counts = [pattern["control"], pattern["hawthorne"], pattern["civic_duty"], pattern["neighbors"], pattern["self"]]
    colors = [LIGHT, GRAY, TEAL, AMBER, NAVY]
    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    left = 0
    for label, count, color in zip(labels, counts, colors):
        ax.barh([0], [count], left=left, color=color, height=0.45, label=label)
        ax.text(left + count / 2, 0, f"{label}\n{count}", ha="center", va="center",
                color="white" if color != LIGHT else NAVY, fontsize=8, fontweight="bold")
        left += count
    ax.set_xlim(0, 18)
    ax.set_yticks([])
    ax.set_xticks(range(0, 19, 2))
    ax.set_xlabel("Households per assignment block")
    fig.suptitle("The design has essentially fixed treatment saturation", x=0.04, y=0.975,
                 ha="left", fontweight="bold", fontsize=12)
    fig.text(0.04, 0.91, "Dominant allocation pattern: 9,997 of 10,000 blocks", color=GRAY, ha="left")
    fig.text(0.5, 0.035,
             "Neighbors share is 1/9 in 9,998 blocks; no within-size variation.\nSpillover dose-response is not identified and is not estimated.",
             ha="center", va="bottom", color=RED, fontweight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout(rect=(0, 0.19, 1, 0.84))
    save_figure(fig, "figure_4_design_interference")


def tables(primary: dict, post: dict, mechanism: dict) -> None:
    manifest = primary["manifest"]
    provenance_rows = [
        ["Repository", "Yale Dataverse", "Official institutional archive"],
        ["Dataset DOI", manifest["dataverse_doi"], "Persistent identifier"],
        ["File ID", str(manifest["data_file_id"]), "Downloaded file"],
        ["Rows", f"{manifest['rows']:,}", "Real administrative voter records"],
        ["Households", f"{manifest['households']:,}", "Unit of treatment assignment"],
        ["Assignment blocks", f"{manifest['blocks']:,}", "Used for randomization inference"],
        ["File bytes", f"{manifest['bytes']:,}", "Integrity metadata"],
        ["SHA-256", manifest["sha256"], "Exact raw-file fingerprint"],
        ["Outcome", "Verified 2006 primary turnout", "Administrative record, not self-report"],
    ]
    write_table("table_1_provenance", ["Field", "Value", "Interpretation"], provenance_rows)

    core = [
        ("Unadjusted voter-level ITT", primary["primary_neighbors_vs_control"]),
        ("Block FE + baseline adjustment", primary["adjusted_block_fixed_effect"]),
        ("Household-level replication", primary["household_level_replication"]),
        ("Exact-duplicate sensitivity", post["exact_duplicate_sensitivity"]),
    ]
    core_rows = []
    for label, r in core:
        lo, hi = ci99(r)
        core_rows.append([label, f"{r['effect']*100:.4f}", f"{r['cluster_se']*100:.4f}",
                          f"[{lo*100:.4f}, {hi*100:.4f}]", fmt_p(r["two_sided_p"]),
                          f"{r['observations']:,}", f"{r['clusters']:,}"])
    ri = primary["block_stratified_randomization_inference"]
    core_rows.append(["Block-stratified randomization inference", f"{ri['observed_effect']*100:.4f}", "-", "-",
                      fmt_p(ri["two_sided_p"]), f"{ri['households']:,}", f"{ri['blocks']:,} blocks"])
    write_table("table_2_core_estimates",
                ["Estimator", "Effect (pp)", "SE (pp)", "99% CI (pp)", "Two-sided p", "N", "Clusters"], core_rows)

    balance_rows = []
    for r in primary["baseline_balance"]:
        balance_rows.append([r["variable"], f"{r['effect']:.5f}", f"{r['standardized_difference']:.4f}",
                             fmt_p(r["two_sided_p"]), fmt_p(r["holm_adjusted_p"])])
    write_table("table_3_balance", ["Baseline", "Raw difference", "Standardized difference", "Raw p", "Holm p"], balance_rows)

    claim_rows = [
        ["Primary", "Household-assignment policy ITT", "Identified", "Neighbors assignment vs control; verified turnout"],
        ["Robustness", "Adjusted and household-level effects", "Supported", "Stable sign and magnitude across prespecified checks"],
        ["Effect modification", "High vs low prior-turnout propensity", "Supported", "Interaction +3.1915 pp; Holm p=4.57e-8"],
        ["Sex modification", "Difference between recorded sex groups", "Not resolved", "Holm p=0.831"],
        ["Household-size modification", "Single vs multi-voter household", "Not resolved", "Holm p=0.255"],
        ["Mechanism", "Every adjacent message component", "Not resolved", "Hawthorne-Civic Holm p=0.066; bundles are not mediators"],
        ["Spillover", "Neighbor-exposure dose-response", "Not identified", "No within-block-size Neighbors-saturation variation"],
        ["Persistence", "Effects in later elections", "External literature only", "Not estimated from the current outcome"],
        ["External validity", "Same 8.13 pp outside study", "Not identified", "Michigan low-salience primary is the target population/context"],
        ["Policy welfare", "Net desirability of deployment", "Not established", "Privacy, autonomy, backlash, and costs require explicit analysis"],
    ]
    write_table("table_4_claim_hierarchy", ["Level", "Claim", "Status", "Reason"], claim_rows)


def main() -> None:
    setup()
    primary = load_json("primary_analysis.json")
    post = load_json("robustness_analysis.json")
    mechanism = load_json("secondary_analysis.json")
    figure_1(primary)
    figure_2(mechanism)
    figure_3(primary, post)
    figure_4(mechanism)
    tables(primary, post, mechanism)
    print("Generated 4 PDF figures, 4 PNG figures, and 8 table files.")


if __name__ == "__main__":
    main()
