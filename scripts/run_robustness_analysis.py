from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from run_primary_analysis import (
    BASELINES,
    cluster_ols,
    coefficient_summary,
    contrast_result,
    holm_adjust,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "GerberGreenLarimer_APSR_2008_social_pressure.tab"
PRIMARY_RESULT = ROOT / "results" / "primary_analysis.json"
OUTPUT = ROOT / "results" / "robustness_analysis.json"


def adjusted_with_g2004(df: pd.DataFrame) -> dict:
    baselines = BASELINES + ["g2004"]
    columns = ["voted", "treatment", "hh_id", "cluster"] + baselines
    use = df.loc[df["treatment"].isin([0, 3]), columns].dropna().copy()
    use["neighbors"] = (use["treatment"] == 3).astype(float)
    variables = ["voted", "neighbors"] + baselines
    demeaned = use[variables] - use.groupby("cluster", observed=False)[variables].transform("mean")
    fit = cluster_ols(
        demeaned["voted"].to_numpy(float),
        demeaned[["neighbors"] + baselines].to_numpy(float),
        use["hh_id"].to_numpy(),
    )
    return coefficient_summary(fit, 0, {"block_fixed_effects": True, "baselines": baselines})


def main() -> None:
    df = pd.read_csv(DATA, sep="\t")
    primary_json = json.loads(PRIMARY_RESULT.read_text(encoding="utf-8"))
    primary = primary_json["primary_neighbors_vs_control"]

    adjusted = adjusted_with_g2004(df)
    critical = float(student_t.ppf(0.995, primary["degrees_of_freedom"]))
    confidence_interval = {
        "level": 0.99,
        "critical_t": critical,
        "lower": float(primary["effect"] - critical * primary["cluster_se"]),
        "upper": float(primary["effect"] + critical * primary["cluster_se"]),
    }

    gradient = primary_json["pressure_gradient"]
    names = ["civic_duty", "hawthorne", "self", "neighbors"]
    holm_values = holm_adjust([gradient[name]["two_sided_p"] for name in names])
    multiplicity = [
        {"treatment": name, "effect": gradient[name]["effect"], "raw_p": gradient[name]["two_sided_p"], "holm_p": p}
        for name, p in zip(names, holm_values)
    ]

    deduplicated = df.drop_duplicates(keep="first")
    duplicate_sensitivity = contrast_result(deduplicated)
    duplicate_sensitivity["rows_removed"] = int(len(df) - len(deduplicated))
    duplicate_sensitivity["effect_change_from_primary"] = float(duplicate_sensitivity["effect"] - primary["effect"])

    primary_sample = df.loc[df["treatment"].isin([0, 3])]
    household_size_transport = {
        "single_voter_household": contrast_result(primary_sample.loc[primary_sample["hh_size"] == 1]),
        "multi_voter_household": contrast_result(primary_sample.loc[primary_sample["hh_size"] > 1]),
    }

    result = {
        "code": "SOCIAL-PRESSURE-ROBUSTNESS",
        "adjusted_with_g2004": adjusted,
        "primary_99pct_confidence_interval": confidence_interval,
        "holm_four_arm_family": multiplicity,
        "exact_duplicate_sensitivity": duplicate_sensitivity,
        "household_size_transport": household_size_transport,
        "identification_boundary": "Household-assignment policy ITT; cross-household interference from neighbor disclosures is possible and not separately identified.",
        "ethics_boundary": "Turnout is public record, but privacy, autonomy, complaints, and removal requests remain material policy costs.",
        "transport_boundary": "Low-salience 2006 Michigan primary; no automatic transport to high-salience elections, other jurisdictions, or digital delivery.",
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
