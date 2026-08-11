import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_result(name: str) -> dict:
    return json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))


def test_primary_estimate_and_design_counts() -> None:
    result = load_result("primary_analysis.json")
    primary = result["primary_neighbors_vs_control"]
    assert abs(primary["effect"] - 0.08130991292051308) < 1e-15
    assert abs(primary["cluster_se"] - 0.00336954742107693) < 1e-15
    assert primary["observations"] == 229444
    assert primary["clusters"] == 119999
    assert result["manifest"]["rows"] == 344084
    assert result["manifest"]["households"] == 180002
    assert result["manifest"]["blocks"] == 10000


def test_robustness_and_uncertainty() -> None:
    result = load_result("robustness_analysis.json")
    interval = result["primary_99pct_confidence_interval"]
    assert abs(interval["lower"] - 0.07263039587473481) < 1e-15
    assert abs(interval["upper"] - 0.08998942996629135) < 1e-15
    assert abs(result["exact_duplicate_sensitivity"]["effect"] - 0.08125326511276969) < 1e-15


def test_secondary_claim_boundaries() -> None:
    result = load_result("secondary_analysis.json")
    interaction = result["heterogeneity"]["interactions"][0]
    assert abs(interaction["effect"] - 0.031915045886225735) < 1e-15
    assert interaction["holm_adjusted_p"] < 1e-7
    assert result["interference_saturation"]["spillover_saturation_identifiable"] is False
    assert result["incremental_pressure"]["all_adjacent_contrasts_resolved"] is False


def test_publication_outputs_exist() -> None:
    expected = [
        ROOT / "output" / "pdf" / "social_pressure_technical_note.pdf",
        ROOT / "output" / "pdf" / "figure_1_pressure_gradient.pdf",
        ROOT / "output" / "pdf" / "figure_2_prior_vote_heterogeneity.pdf",
        ROOT / "output" / "pdf" / "figure_3_robustness_forest.pdf",
        ROOT / "output" / "pdf" / "figure_4_design_interference.pdf",
    ]
    assert all(path.is_file() and path.stat().st_size > 0 for path in expected)

