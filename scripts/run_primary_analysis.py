from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
DATA_ID = 42238
DATA_URL = f"https://dataverse.yale.edu/api/access/datafile/{DATA_ID}"
EXPECTED_SHA256 = "05807BCBEDAACF02EC6E6838E1B9C9B2FC99AD9D8C63F80C162991970044C6CE"
SEED = 2026081183
BASELINES = ["g2002", "g2000", "p2004", "p2002", "p2000", "sex", "yob", "hh_size"]
TREATMENT_LABELS = {0: "control", 1: "hawthorne", 2: "civic_duty", 3: "neighbors", 4: "self"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def download(url: str) -> tuple[bytes, str, str]:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read(), response.geturl(), response.headers.get("Content-Type", "")


def cluster_ols(y: np.ndarray, x: np.ndarray, cluster: np.ndarray) -> dict:
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    cluster = np.asarray(cluster)
    n, k = x.shape
    beta = np.linalg.pinv(x.T @ x) @ (x.T @ y)
    residual = y - x @ beta
    bread = np.linalg.pinv(x.T @ x)
    codes, unique = pd.factorize(cluster, sort=False)
    scores = np.zeros((len(unique), k), dtype=float)
    np.add.at(scores, codes, x * residual[:, None])
    meat = scores.T @ scores
    g = len(unique)
    correction = (g / (g - 1)) * ((n - 1) / (n - k))
    covariance = correction * bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    return {
        "beta": beta,
        "se": se,
        "observations": int(n),
        "clusters": int(g),
        "degrees_of_freedom": int(g - 1),
    }


def coefficient_summary(fit: dict, index: int, extra: dict | None = None) -> dict:
    estimate = float(fit["beta"][index])
    se = float(fit["se"][index])
    statistic = estimate / se if se > 0 else math.inf
    result = {
        "observations": fit["observations"],
        "clusters": fit["clusters"],
        "effect": estimate,
        "cluster_se": se,
        "t_statistic": float(statistic),
        "degrees_of_freedom": fit["degrees_of_freedom"],
        "two_sided_p": float(2 * student_t.sf(abs(statistic), fit["degrees_of_freedom"])),
    }
    if extra:
        result.update(extra)
    return result


def contrast_result(df: pd.DataFrame, treated_code: int = 3) -> dict:
    use = df.loc[df["treatment"].isin([0, treated_code]), ["voted", "treatment", "hh_id"]].dropna()
    treated = (use["treatment"].to_numpy(int) == treated_code).astype(float)
    x = np.column_stack([np.ones(len(use)), treated])
    fit = cluster_ols(use["voted"].to_numpy(float), x, use["hh_id"].to_numpy())
    return coefficient_summary(
        fit,
        1,
        {
            "treated_code": treated_code,
            "treated_label": TREATMENT_LABELS[treated_code],
            "control": int((treated == 0).sum()),
            "treated": int((treated == 1).sum()),
            "control_mean": float(use.loc[treated == 0, "voted"].mean()),
            "treated_mean": float(use.loc[treated == 1, "voted"].mean()),
        },
    )


def adjusted_block_result(df: pd.DataFrame) -> dict:
    columns = ["voted", "treatment", "hh_id", "cluster"] + BASELINES
    use = df.loc[df["treatment"].isin([0, 3]), columns].dropna().copy()
    use["neighbors"] = (use["treatment"] == 3).astype(float)
    variables = ["voted", "neighbors"] + BASELINES
    demeaned = use[variables] - use.groupby("cluster", observed=False)[variables].transform("mean")
    x = demeaned[["neighbors"] + BASELINES].to_numpy(float)
    y = demeaned["voted"].to_numpy(float)
    fit = cluster_ols(y, x, use["hh_id"].to_numpy())
    return coefficient_summary(fit, 0, {"block_fixed_effects": True, "baselines": BASELINES})


def household_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    relevant = df.loc[df["treatment"].isin([0, 3]), ["hh_id", "cluster", "treatment", "voted"]].dropna()
    consistency = relevant.groupby("hh_id", observed=False).agg(
        treatment_nunique=("treatment", "nunique"),
        block_nunique=("cluster", "nunique"),
    )
    inconsistent = int(((consistency["treatment_nunique"] != 1) | (consistency["block_nunique"] != 1)).sum())
    household = relevant.groupby("hh_id", observed=False).agg(
        cluster=("cluster", "first"),
        treatment=("treatment", "first"),
        turnout=("voted", "mean"),
        voters=("voted", "size"),
    ).reset_index()
    household["neighbors"] = (household["treatment"] == 3).astype(int)
    return household, inconsistent


def household_result(household: pd.DataFrame) -> dict:
    x = np.column_stack([np.ones(len(household)), household["neighbors"].to_numpy(float)])
    fit = cluster_ols(household["turnout"].to_numpy(float), x, np.arange(len(household)))
    return coefficient_summary(
        fit,
        1,
        {
            "control_households": int((household["neighbors"] == 0).sum()),
            "treated_households": int((household["neighbors"] == 1).sum()),
            "inference": "HC1 (one observation per household)",
        },
    )


def randomization_inference(household: pd.DataFrame) -> dict:
    ordered = household.sort_values("cluster", kind="stable").reset_index(drop=True)
    labels = ordered["neighbors"].to_numpy(int)
    outcome = ordered["turnout"].to_numpy(float)
    block_values = ordered["cluster"].to_numpy()
    boundaries = np.flatnonzero(np.r_[True, block_values[1:] != block_values[:-1], True])
    segments = [(int(boundaries[i]), int(boundaries[i + 1])) for i in range(len(boundaries) - 1)]
    informative = [(start, stop) for start, stop in segments if 0 < labels[start:stop].sum() < (stop - start)]
    treated_n = int(labels.sum())
    control_n = int(len(labels) - treated_n)
    observed = float(outcome[labels == 1].mean() - outcome[labels == 0].mean())
    rng = np.random.default_rng(SEED)
    exceedances = 0
    permuted = labels.copy()
    for _ in range(999):
        for start, stop in informative:
            permuted[start:stop] = rng.permutation(labels[start:stop])
        draw = float((outcome @ permuted) / treated_n - (outcome @ (1 - permuted)) / control_n)
        exceedances += abs(draw) >= abs(observed)
    return {
        "households": int(len(household)),
        "blocks": int(len(segments)),
        "informative_blocks": int(len(informative)),
        "observed_effect": observed,
        "draws": 999,
        "seed": SEED,
        "exceedances": int(exceedances),
        "two_sided_p": float((exceedances + 1) / 1000),
    }


def holm_adjust(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    m = len(p_values)
    for rank, index in enumerate(order):
        value = min(1.0, (m - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted.tolist()


def balance_results(df: pd.DataFrame) -> list[dict]:
    results = []
    for variable in BASELINES:
        use = df.loc[df["treatment"].isin([0, 3]), [variable, "treatment", "hh_id"]].dropna()
        treated = (use["treatment"].to_numpy(int) == 3).astype(float)
        x = np.column_stack([np.ones(len(use)), treated])
        fit = cluster_ols(use[variable].to_numpy(float), x, use["hh_id"].to_numpy())
        item = coefficient_summary(fit, 1, {"variable": variable})
        a = use.loc[treated == 1, variable].to_numpy(float)
        b = use.loc[treated == 0, variable].to_numpy(float)
        pooled = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)
        item["standardized_difference"] = float(item["effect"] / math.sqrt(pooled))
        results.append(item)
    adjusted = holm_adjust([item["two_sided_p"] for item in results])
    for item, p_value in zip(results, adjusted):
        item["holm_adjusted_p"] = p_value
    return results


def block_influence(df: pd.DataFrame) -> dict:
    use = df.loc[df["treatment"].isin([0, 3]), ["cluster", "treatment", "voted"]].dropna().copy()
    use["neighbors"] = (use["treatment"] == 3).astype(int)
    total = use.groupby("neighbors")["voted"].agg(["sum", "count"])
    by_block = use.groupby(["cluster", "neighbors"])["voted"].agg(["sum", "count"]).unstack(fill_value=0)
    effects = []
    for block, row in by_block.iterrows():
        treated_mean = (total.loc[1, "sum"] - row[("sum", 1)]) / (total.loc[1, "count"] - row[("count", 1)])
        control_mean = (total.loc[0, "sum"] - row[("sum", 0)]) / (total.loc[0, "count"] - row[("count", 0)])
        effects.append((str(block), float(treated_mean - control_mean)))
    minimum = min(effects, key=lambda item: item[1])
    maximum = max(effects, key=lambda item: item[1])
    return {
        "blocks": len(effects),
        "minimum": minimum[1],
        "minimum_block": minimum[0],
        "maximum": maximum[1],
        "maximum_block": maximum[0],
        "span": maximum[1] - minimum[1],
    }


def transport_results(df: pd.DataFrame) -> dict:
    primary = df.loc[df["treatment"].isin([0, 3])].copy()
    primary["prior_votes"] = primary[["g2002", "g2000", "p2004", "p2002", "p2000"]].sum(axis=1, min_count=5)
    return {
        "sex_0": contrast_result(primary.loc[primary["sex"] == 0]),
        "sex_1": contrast_result(primary.loc[primary["sex"] == 1]),
        "prior_low_0_2": contrast_result(primary.loc[primary["prior_votes"] <= 2]),
        "prior_high_3_5": contrast_result(primary.loc[primary["prior_votes"] >= 3]),
    }


def observation_result(df: pd.DataFrame) -> dict:
    use = df.loc[df["treatment"].isin([0, 3]), ["voted", "treatment", "hh_id", "cluster"]].dropna(
        subset=["treatment", "hh_id", "cluster"]
    ).copy()
    use["observed"] = use["voted"].notna().astype(float)
    treated = (use["treatment"].to_numpy(int) == 3).astype(float)
    y = use["observed"].to_numpy(float)
    if np.ptp(y) == 0:
        return {"observations": len(use), "households": int(use["hh_id"].nunique()), "effect": 0.0, "cluster_se": 0.0, "two_sided_p": 1.0}
    fit = cluster_ols(y, np.column_stack([np.ones(len(use)), treated]), use["hh_id"].to_numpy())
    return coefficient_summary(fit, 1)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    data_bytes, final_url, content_type = download(DATA_URL)
    observed_sha256 = sha256_bytes(data_bytes)
    if observed_sha256 != EXPECTED_SHA256:
        raise RuntimeError(
            f"Downloaded data hash mismatch: expected {EXPECTED_SHA256}, observed {observed_sha256}"
        )
    data_path = RAW / "GerberGreenLarimer_APSR_2008_social_pressure.tab"
    data_path.write_bytes(data_bytes)
    df = pd.read_csv(data_path, sep="\t")
    required = ["treatment", "voted", "hh_id", "cluster"] + BASELINES
    missing_fields = sorted(set(required) - set(df.columns))
    if missing_fields:
        raise RuntimeError(f"Missing required fields: {missing_fields}; schema={list(df.columns)}")
    for variable in ["treatment", "voted", "g2002", "g2000", "p2004", "p2002", "p2000", "sex"]:
        values = set(df[variable].dropna().unique().tolist())
        allowed = set(TREATMENT_LABELS) if variable == "treatment" else {0, 1}
        if not values.issubset(allowed):
            raise RuntimeError(f"Unexpected values for {variable}: {sorted(values)}")

    household, inconsistent_households = household_frame(df)
    primary = contrast_result(df)
    adjusted = adjusted_block_result(df)
    household_replication = household_result(household)
    randomization = randomization_inference(household)
    gradient = {TREATMENT_LABELS[code]: contrast_result(df, code) for code in [2, 1, 4, 3]}
    balance = balance_results(df)
    influence = block_influence(df)
    transport = transport_results(df)
    observation = observation_result(df)

    result = {
        "code": "SOCIAL-PRESSURE-TURNOUT-RCT",
        "name": "Neighbors social-pressure mailer and verified voter turnout",
        "source_disclosure": "The published article reported positive treatment results before this benchmark replication was conducted.",
        "manifest": {
            "dataverse_doi": "10.60600/YU/CGMWNW",
            "data_file_id": DATA_ID,
            "requested_url": DATA_URL,
            "final_url": final_url,
            "content_type": content_type,
            "bytes": len(data_bytes),
            "sha256": sha256_bytes(data_bytes),
            "rows": int(len(df)),
            "columns": list(df.columns),
            "missing_by_required_column": {column: int(df[column].isna().sum()) for column in required},
            "households": int(df["hh_id"].nunique(dropna=True)),
            "blocks": int(df["cluster"].nunique(dropna=True)),
            "duplicate_full_rows": int(df.duplicated().sum()),
            "inconsistent_primary_households": inconsistent_households,
        },
        "primary_neighbors_vs_control": primary,
        "adjusted_block_fixed_effect": adjusted,
        "household_level_replication": household_replication,
        "block_stratified_randomization_inference": randomization,
        "pressure_gradient": gradient,
        "baseline_balance": balance,
        "leave_one_block_out": influence,
        "transport": transport,
        "outcome_observation": observation,
        "claim_boundary": "Experimental ITT of the Neighbors mailer on verified 2006 Michigan primary turnout in the study population.",
    }
    output = RESULTS / "primary_analysis.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
