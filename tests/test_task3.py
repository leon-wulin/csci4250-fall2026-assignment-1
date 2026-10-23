"""Task 3 scope, normalization, fitting support and export tests on small fixtures."""
import json
import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "results/cache/task3_mpl"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import networkx as nx
import numpy as np
import pytest
from PIL import Image
from src.task2_core import analyze_cached, calculate_global_properties
from src.task3_distributions import (METRICS, collect_samples, empirical_frequencies,
                                     clustering_bins, statistics, validate_samples)
from src.task3_fitting import (candidate_cdf, candidate_pmf, curve_rows, fit_distribution,
                              ks_distance, choose, unavailable)
from src.task3_plotting import render_composite

CONFIG = json.loads((ROOT / "task3_config.json").read_text())


def test_discrete_frequency_preserves_zero_and_empty_bins():
    rows = empirical_frequencies(np.array([0, 0, 1, 3]), "degree")
    assert [row["count"] for row in rows] == [2, 1, 0, 1]
    assert [row["probability"] for row in rows] == [0.5, 0.25, 0, 0.25]


def test_clustering_endpoint_atoms_not_mixed_into_interior_bins():
    values = np.array([0, 0, 1e-16, 0.25, 0.5, 1])
    rows = clustering_bins(values, 4)
    assert rows[0]["count"] == 2 and rows[-1]["count"] == 1
    assert sum(row["count"] for row in rows) == 6
    assert sum(row["count"] for row in rows if row["kind"] == "interior_bin") == 3
    assert sum(row["probability"] for row in rows) == pytest.approx(1)


@pytest.mark.parametrize("values", [[], [np.nan], [np.inf]])
def test_nonfinite_or_empty_samples_rejected(values):
    with pytest.raises(ValueError):
        statistics(np.asarray(values))


def test_actual_scope_and_cache_reuse_without_bfs(tmp_path, monkeypatch):
    graph = nx.disjoint_union(nx.path_graph(4), nx.complete_graph(3))
    graph.add_node(99)
    result, _ = analyze_cached(graph, "fixture_real", tmp_path / "results/cache", {}, logging.getLogger("test-task3"))

    def forbidden(*args, **kwargs):
        raise AssertionError("Task 3 must reuse eccentricity data")

    monkeypatch.setattr(nx, "single_source_shortest_path_length", forbidden)
    monkeypatch.setattr(nx, "eccentricity", forbidden)
    samples, ids = collect_samples(tmp_path, "fixture_real", graph)
    validate_samples("fixture_real", graph, samples, result)
    assert ids["eccentricity"] == [0, 1, 2, 3]
    assert len(samples["degree"]) == len(samples["clustering"]) == 8
    assert samples["eccentricity"].tolist() == [3, 2, 2, 3]
    assert samples["component_size"].tolist() == [4, 3, 1]
    assert statistics(samples["clustering"])["mean"] == 3 / 8
    assert statistics(samples["component_size"])["mean"] == pytest.approx(8 / 3)
    assert statistics(samples["component_size"])["population_variance"] == pytest.approx(14 / 9)


@pytest.mark.parametrize("metric", ["clustering", "component_size", "eccentricity"])
def test_degenerate_distributions_are_not_forced_to_fit(metric):
    values = np.zeros(100) if metric == "clustering" else np.array([20]) if metric == "component_size" else np.repeat(3, 100)
    fit = fit_distribution(values, metric, "real", None, CONFIG)
    assert fit["status"] == "N/A" and fit["reason"]
    assert curve_rows(fit, empirical_frequencies(values, metric)) == []
    assert statistics(values)["population_variance"] == 0


def test_er_reference_uses_recorded_probability_not_realized_mean():
    values = np.repeat([0, 1, 2], [30, 50, 20])
    fit = fit_distribution(values, "degree", "er", {"n": 100, "p": 0.03}, CONFIG)
    assert fit["parameters"] == {"trials": 99, "p": 0.03}
    assert fit["status"] == "model_reference"
    assert sum(candidate_pmf(fit, np.arange(100))) == pytest.approx(1)


def test_beta_mixture_returns_bin_mass_and_preserves_atoms():
    values = np.concatenate([np.zeros(100), np.linspace(0.01, 0.99, 500), np.ones(50)])
    fit = fit_distribution(values, "clustering", "real", None, CONFIG)
    assert fit["method"] == "zero_one_inflated_beta"
    rows = curve_rows(fit, empirical_frequencies(values, "clustering"), clustering_bins(values, 20))
    assert rows[0]["probability"] == pytest.approx(100 / 650)
    assert rows[-1]["probability"] == pytest.approx(50 / 650)
    assert sum(row["probability"] for row in rows) == pytest.approx(1)


def test_eccentricity_candidates_use_integer_bounded_support():
    values = np.repeat(np.arange(2, 9), [5, 40, 160, 250, 160, 40, 5])
    fit = fit_distribution(values, "eccentricity", "real", None, CONFIG)
    assert fit["status"] == "descriptive_fit"
    assert candidate_cdf(fit, np.array([1, 8])).tolist() == pytest.approx([0, 1])
    assert sum(candidate_pmf(fit, np.arange(2, 9))) == pytest.approx(1)


def test_reflected_kde_fallback_is_normalized_and_keeps_endpoint_atoms():
    values = np.concatenate([np.zeros(50), np.repeat([0.05, 0.15, 0.45, 0.85], [70, 10, 10, 10]), np.ones(30)])
    fit = fit_distribution(values, "clustering", "real", None, CONFIG)
    assert fit["method"] == "reflected_kde_mixture" and fit["status"] == "descriptive_smoother"
    assert fit["aic"] is None
    rows = curve_rows(fit, empirical_frequencies(values, "clustering"), clustering_bins(values, 20))
    assert sum(row["probability"] for row in rows) == pytest.approx(1)
    assert rows[0]["probability"] == 50 / 180 and rows[-1]["probability"] == 30 / 180


def test_discrete_tail_mle_and_body_not_fitted():
    values = np.random.default_rng(123).zipf(2.7, size=900)
    fit = fit_distribution(values, "degree", "ba", None, CONFIG)
    assert fit["status"] == "descriptive_fit"
    power = next(c for c in fit["candidates"] if c["method"] == "discrete_power_law_tail")
    assert 2 < power["parameters"]["alpha"] < 3.5
    curves = curve_rows(fit, empirical_frequencies(values, "degree"))
    assert all(row["value"] >= fit["xmin_search"]["selected_xmin"] for row in curves)


def test_ks_checks_left_and_right_integer_jumps():
    assert ks_distance(np.array([1, 1, 3, 3]), lambda x: np.where(x < 1, 0, np.where(x < 3, 0.5, 1))) == 0


def test_poor_candidates_explicitly_marked_na():
    fit = choose([{"method": "bad", "parameters": {}, "ks": 0.6, "aic": 1}], CONFIG, "fixture")
    assert fit["status"] == "N/A" and "mismatch" in fit["reason"]


def test_composite_exports_three_panels_and_retains_zero(tmp_path):
    values = np.array([0, 1, 1, 2, 2])
    entry = {"statistics": statistics(values), "fit": unavailable("Small fixture; no shape fit.", "all nodes"),
             "frequencies": empirical_frequencies(values, "degree"), "bins": None,
             "curves": [], "graph_nodes": 5, "graph_edges": 3}
    records = {"grqc_" + model: {"degree": entry} for model in ("real", "er", "ba")}
    info = render_composite("grqc", "degree", records, tmp_path, CONFIG)
    assert len(info["panels"]) == 3 and info["empirical_observations_plotted"] == [5, 5, 5]
    assert info["all_text_inside_canvas"]
    with Image.open(tmp_path / "grqc__degree.png") as image:
        assert image.width == 3000 and image.height == 1160
    pdf = (tmp_path / "grqc__degree.pdf").read_bytes()
    assert pdf.startswith(b"%PDF") and b"/Subtype /Image" not in pdf
