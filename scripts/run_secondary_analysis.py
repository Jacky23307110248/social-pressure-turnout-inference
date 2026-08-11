from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from run_primary_analysis import contrast_result, holm_adjust


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "GerberGreenLarimer_APSR_2008_social_pressure.tab"
OUTPUT = ROOT / "results" / "secondary_analysis.json"
BASELINES = ["g2002", "g2000", "p2004", "p2002", "p2000", "sex", "yob", "hh_size", "g2004"]
DUMMY_CODES = [2, 1, 4, 3]
DUMMY_NAMES = ["civic_duty", "hawthorne", "self", "neighbors"]


def cluster_fit(y: np.ndarray, x: np.ndarray, cluster: np.ndarray) -> dict:
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    n, k = x.shape
    beta = np.linalg.pinv(x.T @ x) @ (x.T @ y)
    residual = y - x @ beta
    bread = np.linalg.pinv(x.T @ x)
    codes, unique = pd.factorize(cluster, sort=False)
    scores = np.zeros((len(unique), k), dtype=float)
    np.add.at(scores, codes, x * residual[:, None])
    correction = (len(unique) / (len(unique) - 1)) * ((n - 1) / (n - k))
    covariance = correction * bread @ (scores.T @ scores) @ bread
    return {
        "beta": beta,
        "covariance": covariance,
        "observations": int(n),
        "clusters": int(len(unique)),
        "df": int(len(unique) - 1),
    }


def contrast(fit: dict, weights: np.ndarray, name: str) -> dict:
    estimate = float(weights @ fit["beta"])
    se = float(math.sqrt(max(0.0, weights @ fit["covariance"] @ weights)))
    statistic = estimate / se
    return {
        "contrast": name,
        "effect": estimate,
        "cluster_se": se,
        "t_statistic": statistic,
        "degrees_of_freedom": fit["df"],
        "two_sided_p": float(2 * student_t.sf(abs(statistic), fit["df"])),
    }


def incremental_models(df: pd.DataFrame) -> dict:
    use = df[["voted", "treatment", "hh_id", "cluster"] + BASELINES].dropna().copy()
    dummies = np.column_stack([(use["treatment"].to_numpy(int) == code).astype(float) for code in DUMMY_CODES])
    raw_x = np.column_stack([np.ones(len(use)), dummies])
    raw_fit = cluster_fit(use["voted"].to_numpy(float), raw_x, use["hh_id"].to_numpy())

    variable_frame = pd.DataFrame(dummies, columns=DUMMY_NAMES, index=use.index)
    for variable in BASELINES:
        variable_frame[variable] = use[variable].to_numpy(float)
    demeaned_x = variable_frame - variable_frame.groupby(use["cluster"], observed=False).transform("mean")
    demeaned_y = use["voted"] - use.groupby("cluster", observed=False)["voted"].transform("mean")
    adjusted_fit = cluster_fit(demeaned_y.to_numpy(float), demeaned_x.to_numpy(float), use["hh_id"].to_numpy())

    raw_weights = [
        np.array([0, 1, 0, 0, 0], float),
        np.array([0, -1, 1, 0, 0], float),
        np.array([0, 0, -1, 1, 0], float),
        np.array([0, 0, 0, -1, 1], float),
    ]
    adjusted_weights = [weights[1:].tolist() + [0.0] * len(BASELINES) for weights in raw_weights]
    names = ["civic_minus_control", "hawthorne_minus_civic", "self_minus_hawthorne", "neighbors_minus_self"]
    raw = [contrast(raw_fit, weights, name) for weights, name in zip(raw_weights, names)]
    adjusted = [contrast(adjusted_fit, np.asarray(weights), name) for weights, name in zip(adjusted_weights, names)]
    adjusted_holm = holm_adjust([item["two_sided_p"] for item in adjusted])
    for item, p_value in zip(adjusted, adjusted_holm):
        item["holm_adjusted_p"] = p_value
    return {
        "raw": raw,
        "block_baseline_adjusted": adjusted,
        "all_adjacent_contrasts_resolved": all(item["effect"] > 0 and item["holm_adjusted_p"] <= 0.05 for item in adjusted),
    }


def interaction_result(df: pd.DataFrame, subgroup: pd.Series, name: str) -> dict:
    use = df.loc[df["treatment"].isin([0, 3]), ["voted", "treatment", "hh_id"]].copy()
    use["subgroup"] = subgroup.loc[use.index]
    use = use.dropna()
    treatment = (use["treatment"].to_numpy(int) == 3).astype(float)
    group = use["subgroup"].to_numpy(float)
    x = np.column_stack([np.ones(len(use)), treatment, group, treatment * group])
    fit = cluster_fit(use["voted"].to_numpy(float), x, use["hh_id"].to_numpy())
    item = contrast(fit, np.array([0, 0, 0, 1], float), name)
    item["reference_effect"] = float(fit["beta"][1])
    item["subgroup_effect"] = float(fit["beta"][1] + fit["beta"][3])
    item["observations"] = fit["observations"]
    return item


def heterogeneity(df: pd.DataFrame) -> dict:
    prior_votes = df[["g2002", "g2000", "p2004", "p2002", "p2000"]].sum(axis=1, min_count=5)
    interactions = [
        interaction_result(df, (prior_votes >= 3).astype(float), "high_minus_low_prior_propensity"),
        interaction_result(df, df["sex"].astype(float), "sex_1_minus_sex_0"),
        interaction_result(df, (df["hh_size"] == 1).astype(float), "single_minus_multi_voter_household"),
    ]
    adjusted_p = holm_adjust([item["two_sided_p"] for item in interactions])
    for item, p_value in zip(interactions, adjusted_p):
        item["holm_adjusted_p"] = p_value
        item["material_and_resolved"] = abs(item["effect"]) >= 0.01 and p_value <= 0.05

    prior_bins = []
    for score in range(6):
        item = contrast_result(df.loc[prior_votes == score])
        item["prior_vote_score"] = score
        prior_bins.append(item)
    bin_adjusted = holm_adjust([item["two_sided_p"] for item in prior_bins])
    for item, p_value in zip(prior_bins, bin_adjusted):
        item["holm_adjusted_p"] = p_value
    return {"interactions": interactions, "prior_vote_score_bins": prior_bins}


def saturation_audit(df: pd.DataFrame) -> dict:
    household = df.groupby("hh_id", observed=False).agg(
        block=("cluster", "first"),
        block_nunique=("cluster", "nunique"),
        treatment=("treatment", "first"),
        treatment_nunique=("treatment", "nunique"),
    ).reset_index()
    inconsistent = int(((household["block_nunique"] != 1) | (household["treatment_nunique"] != 1)).sum())
    counts = pd.crosstab(household["block"], household["treatment"]).reindex(columns=range(5), fill_value=0)
    counts.columns = ["control", "hawthorne", "civic_duty", "neighbors", "self"]
    counts["block_size"] = counts.sum(axis=1)
    counts["neighbors_share"] = counts["neighbors"] / counts["block_size"]
    patterns = counts.value_counts().reset_index(name="blocks")
    pattern_records = patterns.to_dict(orient="records")
    share_frequencies = counts["neighbors_share"].value_counts().sort_index()
    qualifying = share_frequencies.loc[share_frequencies >= 100]
    within_size_variation = counts.groupby("block_size")["neighbors_share"].nunique().max()
    identifiable = len(qualifying) >= 3 and int(within_size_variation) >= 3
    return {
        "households": int(len(household)),
        "blocks": int(len(counts)),
        "inconsistent_households": inconsistent,
        "allocation_patterns": pattern_records,
        "neighbors_share_frequencies": {str(float(key)): int(value) for key, value in share_frequencies.items()},
        "maximum_distinct_neighbor_shares_within_block_size": int(within_size_variation),
        "spillover_saturation_identifiable": bool(identifiable),
        "decision": "Do not estimate spillovers" if not identifiable else "Saturation analysis feasible",
    }


def main() -> None:
    df = pd.read_csv(DATA, sep="\t")
    result = {
        "code": "SOCIAL-PRESSURE-SECONDARY",
        "incremental_pressure": incremental_models(df),
        "heterogeneity": heterogeneity(df),
        "interference_saturation": saturation_audit(df),
        "claim_boundary": "Incremental contrasts identify bundled message-arm differences; they are not mediation effects. Spillovers are not estimated without saturation support.",
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
