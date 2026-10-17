"""Small reference tests for the proposed methods, not production analysis code."""
from __future__ import annotations

import runpy
from pathlib import Path

import networkx as nx
import numpy as np
import pytest


def summarize_fixture(graph: nx.Graph) -> dict:
    """Use full-graph non-distance statistics and one exact BFS per LCC node."""
    if graph.is_directed() or not 0 < len(graph) <= 32:
        raise ValueError("Only tiny nonempty undirected fixtures are allowed")
    components = sorted(nx.connected_components(graph), key=lambda nodes: (-len(nodes), min(nodes)))
    lcc = graph.subgraph(components[0])
    eccentricities = {node: max(nx.single_source_shortest_path_length(lcc, node).values()) for node in lcc}
    degree = np.array([value for _, value in graph.degree()], dtype=float)
    clustering = np.array(list(nx.clustering(graph).values()), dtype=float)
    sizes = np.array([len(nodes) for nodes in components], dtype=float)
    ecc = np.array(list(eccentricities.values()), dtype=float)
    return {
        "degree_mean": degree.mean(), "degree_variance": degree.var(ddof=0),
        "degree_sum": degree.sum(), "components": len(components), "lcc": len(lcc),
        "component_mean": sizes.mean(), "component_variance": sizes.var(ddof=0),
        "clustering_mean": clustering.mean(), "clustering_variance": clustering.var(ddof=0),
        "diameter": ecc.max(), "radius": ecc.min(), "ecc_mean": ecc.mean(),
        "ecc_variance": ecc.var(ddof=0), "eccentricities": eccentricities,
    }


def test_path_with_isolate_and_single_bfs_pass(monkeypatch):
    graph = nx.path_graph(4)
    graph.add_node(4)
    bfs = nx.single_source_shortest_path_length
    calls = []

    def counted_bfs(graph, node):
        calls.append(node)
        return bfs(graph, node)

    monkeypatch.setattr(nx, "single_source_shortest_path_length", counted_bfs)
    result = summarize_fixture(graph)
    expected = {"degree_mean": 1.2, "degree_variance": 0.56, "degree_sum": 6,
                "components": 2, "lcc": 4, "component_mean": 2.5,
                "component_variance": 2.25, "clustering_mean": 0,
                "clustering_variance": 0, "diameter": 3, "radius": 2,
                "ecc_mean": 2.5, "ecc_variance": 0.25}
    for key, value in expected.items():
        assert result[key] == pytest.approx(value)
    assert result["eccentricities"] == {0: 3, 1: 2, 2: 2, 3: 3}
    assert sorted(calls) == [0, 1, 2, 3]


def test_triangle_with_isolate_clustering_uses_full_graph():
    graph = nx.complete_graph(3)
    graph.add_node(3)
    result = summarize_fixture(graph)
    assert result["degree_mean"] == 1.5
    assert result["degree_variance"] == 0.75
    assert result["clustering_mean"] == 0.75
    assert result["clustering_variance"] == 0.1875
    assert result["component_mean"] == 2
    assert result["component_variance"] == 1
    assert result["ecc_mean"] == result["diameter"] == result["radius"] == 1


@pytest.mark.parametrize("graph,diameter,radius,ecc_mean,ecc_var", [
    (nx.star_graph(3), 2, 1, 1.75, 0.1875),
    (nx.cycle_graph(4), 2, 2, 2, 0),
    (nx.empty_graph(1), 0, 0, 0, 0),
])
def test_known_distance_properties(graph, diameter, radius, ecc_mean, ecc_var):
    result = summarize_fixture(graph)
    assert result["diameter"] == diameter
    assert result["radius"] == radius
    assert result["ecc_mean"] == ecc_mean
    assert result["ecc_variance"] == ecc_var
    assert all(np.isfinite(value) for key, value in result.items() if key != "eccentricities")


def test_reference_parameters_without_generating_large_graphs():
    methods = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/inspect_datasets.py"))
    parameters = methods["planned_parameters"]
    for n, edges, expected_m, expected_ba in [(5242, 14496, 3, 15717), (5242, 14484, 3, 15717), (4941, 6594, 1, 4940)]:
        result = parameters(n, edges)
        assert result["er_p"] * n * (n - 1) / 2 == pytest.approx(edges)
        assert result["ba_m"] == expected_m
        assert result["ba_formula_edges"] == expected_ba
    assert abs(4940 - 6594) < abs(9878 - 6594)
    assert len(set(methods["PLANNED_SEEDS"].values())) == 4


def test_small_er_reproducibility_and_whole_graph_statistics():
    first = nx.gnp_random_graph(24, 0.05, seed=2026101701)
    second = nx.gnp_random_graph(24, 0.05, seed=2026101701)
    assert set(first.edges) == set(second.edges)
    assert len(first) == 24
    assert sum(dict(first.degree()).values()) == 2 * first.number_of_edges()
    assert summarize_fixture(first)["degree_mean"] == pytest.approx(2 * first.number_of_edges() / 24)


@pytest.mark.parametrize("m", [1, 2, 3])
def test_small_standard_ba_formula_and_seed(m):
    graph = nx.barabasi_albert_graph(24, m, seed=2026101702)
    repeat = nx.barabasi_albert_graph(24, m, seed=2026101702)
    assert len(graph) == 24
    assert graph.number_of_edges() == m * (24 - m)
    assert set(graph.edges) == set(repeat.edges)
    if m == 1:
        assert nx.is_tree(graph)
        assert nx.average_clustering(graph) == 0


def test_self_loop_policy_changes_edge_count_but_not_nodes():
    raw = nx.path_graph(4)
    raw.add_edge(0, 0)
    proposed = raw.copy()
    proposed.remove_edges_from(nx.selfloop_edges(proposed))
    assert raw.number_of_edges() == 4 and nx.number_of_selfloops(raw) == 1
    assert proposed.number_of_edges() == 3 and nx.number_of_selfloops(proposed) == 0
    assert set(raw) == set(proposed)
    assert sum(dict(raw.degree()).values()) == 2 * raw.number_of_edges()


def test_audit_refuses_output_into_raw_sources(monkeypatch, capsys):
    path = Path(__file__).resolve().parents[1] / "scripts/inspect_datasets.py"
    methods = runpy.run_path(str(path))
    source = path.parents[1] / "data/raw/power/power.gml"
    monkeypatch.setattr(methods["sys"], "argv", [str(path), "--output", str(source)])
    with pytest.raises(SystemExit) as error:
        methods["main"]()
    assert error.value.code == 2
    assert "source inputs are read-only" in capsys.readouterr().err
