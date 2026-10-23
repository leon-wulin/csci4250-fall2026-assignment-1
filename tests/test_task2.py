"""Known mathematical fixtures and artifact/invalidation tests for production code."""
from __future__ import annotations

import csv
import json
import logging

import networkx as nx
import pytest

from src.task2_core import (
    METRIC_FIELDS, TABLE_FIELDS, analyze_cached, cache_identity, cache_paths,
    calculate_global_properties, generate_models, graph_fingerprint, preprocess_graph,
    save_graph, summarize, validate_cache, validate_graph, write_csv, write_json,
)
from src.run_task2 import IDS, MODEL_FIELDS, verify_outputs


@pytest.mark.parametrize("graph,expected", [
    (nx.path_graph(4), (4, 3, 1, 4, 3, 2, 2.5, 1.5, 0.25)),
    (nx.complete_graph(5), (5, 10, 1, 5, 1, 1, 1.0, 4.0, 0.0)),
    (nx.disjoint_union(nx.path_graph(4), nx.complete_graph(3)), (7, 6, 2, 4, 3, 2, 2.5, 12 / 7, 10 / 49)),
    (nx.empty_graph(3), (3, 0, 3, 1, 0, 0, 0.0, 0.0, 0.0)),
    (nx.star_graph(3), (4, 3, 1, 4, 2, 1, 1.75, 1.5, 0.75)),
    (nx.cycle_graph(5), (5, 5, 1, 5, 2, 2, 2.0, 2.0, 0.0)),
])
def test_known_properties(graph, expected):
    result, ecc = calculate_global_properties(graph)
    for key, value in zip(METRIC_FIELDS, expected):
        assert result[key] == pytest.approx(value)
    assert ecc == nx.eccentricity(graph.subgraph(ecc))
    assert result["diameter"] >= result["radius"]
    assert result["radius"] <= result["average_eccentricity"] <= result["diameter"]
    assert result["lcc_size"] <= len(graph)
    assert sum(map(len, nx.connected_components(graph))) == len(graph)


def test_full_graph_degree_scope_and_once_only_bfs(monkeypatch):
    graph = nx.path_graph(4)
    graph.add_node(99)
    original = nx.single_source_shortest_path_length
    calls = []

    def counted(graph, source):
        calls.append(source)
        return original(graph, source)

    monkeypatch.setattr(nx, "single_source_shortest_path_length", counted)
    result, ecc = calculate_global_properties(graph)
    assert sorted(calls) == [0, 1, 2, 3]
    assert ecc == {0: 3, 1: 2, 2: 2, 3: 3}
    assert result["average_degree"] == pytest.approx(1.2)
    assert result["degree_variance"] == pytest.approx(0.56)
    assert result["number_of_components"] == 2
    assert result["isolates"] == 1
    assert result["average_eccentricity"] == 2.5


def test_lcc_tie_uses_smallest_numeric_id():
    graph = nx.Graph([(8, 9), (1, 2)])
    _, ecc = calculate_global_properties(graph)
    assert set(ecc) == {1, 2}


def test_preprocessing_preserves_raw_graph_and_isolates():
    raw = nx.path_graph(4)
    raw.add_edge(0, 0)
    raw.add_node(90)
    before = graph_fingerprint(raw)
    with pytest.raises(ValueError, match="policy not approved"):
        preprocess_graph(raw, remove_self_loops=False)
    graph, metadata = preprocess_graph(raw, remove_self_loops=True)
    assert graph_fingerprint(raw) == before
    assert set(graph) == set(raw)
    assert metadata["removed_self_loop_nodes"] == [0]
    assert metadata["original_edges"] == 4
    assert metadata["analyzed_edges"] == 3
    assert graph.degree(90) == 0


@pytest.mark.parametrize("kind", ["empty", "directed", "multi", "weighted", "loop", "noninteger"])
def test_invalid_inputs_rejected(kind):
    graph = nx.path_graph(3)
    if kind == "empty":
        graph = nx.Graph()
    elif kind == "directed":
        graph = nx.DiGraph(graph)
    elif kind == "multi":
        graph = nx.MultiGraph(graph)
    elif kind == "weighted":
        graph[0][1]["weight"] = 1
    elif kind == "loop":
        graph.add_edge(0, 0)
    else:
        graph = nx.relabel_nodes(graph, {0: "author"})
    with pytest.raises(ValueError):
        validate_graph(graph)


@pytest.mark.parametrize("n,edges,m", [(24, 22, 1), (30, 80, 3), (10, 9, 1)])
def test_models_exact_seed_and_closest_ba(n, edges, m):
    real = nx.empty_graph(n)
    real.add_edges_from(list(nx.complete_graph(n).edges)[:edges])
    first = generate_models(real, family="fixture", seed=42)
    second = generate_models(real, family="fixture", seed=42)
    for (identifier, graph, params), (_, repeat, _) in zip(first, second):
        assert len(graph) == n
        assert graph_fingerprint(graph) == graph_fingerprint(repeat)
        assert params["seed"] == 42
        assert params["absolute_edge_difference"] == abs(graph.number_of_edges() - edges)
        assert params["relative_edge_difference"] == pytest.approx(abs(graph.number_of_edges() - edges) / edges)
        if identifier.endswith("_ba"):
            assert params["m"] == m
            assert graph.number_of_edges() == m * (n - m)
            assert abs(graph.number_of_edges() - edges) == min(abs(k * (n - k) - edges) for k in range(1, n))
        else:
            assert params["p"] == 2 * edges / (n * (n - 1))


def test_graphml_retains_isolates_and_node_ids(tmp_path):
    graph = nx.Graph([(17, 31)])
    graph.add_node(100)
    path = tmp_path / "test.graphml"
    save_graph(path, graph)
    restored = nx.read_graphml(path, node_type=int)
    assert set(restored) == {17, 31, 100}
    assert restored.degree(100) == 0
    assert graph_fingerprint(restored) == graph_fingerprint(graph)
    graph.add_node(200)
    assert graph_fingerprint(restored) != graph_fingerprint(graph)


def test_cache_reuse_invalidation_and_tamper_rejection(tmp_path, monkeypatch):
    graph = nx.path_graph(5)
    context = {"seed": 42, "code_version": "test"}
    logger = logging.getLogger("test-task2")
    original, hit = analyze_cached(graph, "fixture", tmp_path, context, logger)
    assert not hit
    bfs = nx.single_source_shortest_path_length

    def unexpected(*args, **kwargs):
        raise AssertionError("Completed unchanged cache must not recompute BFS")

    monkeypatch.setattr(nx, "single_source_shortest_path_length", unexpected)
    reused, hit = analyze_cached(graph, "fixture", tmp_path, context, logger)
    assert hit and reused == original
    monkeypatch.setattr(nx, "single_source_shortest_path_length", bfs)
    _, hit = analyze_cached(graph, "fixture", tmp_path, {"seed": 43}, logger)
    assert not hit
    path = cache_paths(tmp_path, "fixture")["eccentricity"]
    path.write_text("network_id,node_id,eccentricity\nfixture,0,99\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Corrupted"):
        validate_cache(tmp_path, "fixture", graph, cache_identity(graph, {"seed": 43}))


def test_interruption_preserves_previously_completed_network(tmp_path, monkeypatch):
    logger = logging.getLogger("test-task2-interrupted")
    graph = nx.path_graph(4)
    analyze_cached(graph, "finished", tmp_path, {}, logger)

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt("synthetic interruption")

    monkeypatch.setattr(nx, "single_source_shortest_path_length", interrupted)
    with pytest.raises(KeyboardInterrupt):
        analyze_cached(graph, "interrupted", tmp_path, {}, logger)
    assert not cache_paths(tmp_path, "interrupted")["manifest"].exists()
    assert analyze_cached(graph, "finished", tmp_path, {}, logger)[1]


def test_invalid_eccentricity_scope_or_values_rejected():
    graph = nx.path_graph(4)
    for ecc in ({0: 3}, {0: 99, 1: 2, 2: 2, 3: 3}, {0: 0, 1: 2, 2: 2, 3: 3}):
        with pytest.raises(ValueError):
            summarize(graph, ecc)


def test_six_fixture_output_integration_and_csv_json_consistency(tmp_path):
    context, graphs, models, results = {}, {}, {}, {}
    logger = logging.getLogger("test-task2-integration")
    for family in ("grqc", "power"):
        graph = nx.path_graph(8)
        graph.add_node(20)
        graphs[family + "_real"] = graph
        for identifier, generated, params in generate_models(graph, family=family, seed=42):
            params["reference_graph_fingerprint"] = graph_fingerprint(graph)
            models[identifier] = params
            graphs[identifier] = generated
    for identifier in IDS:
        path = tmp_path / f"data/processed/task2/{identifier}.graphml"
        save_graph(path, graphs[identifier])
        stats, _ = analyze_cached(graphs[identifier], identifier, tmp_path / "results/cache", context, logger)
        results[identifier] = {**stats, "network_id": identifier, "family": identifier.split("_")[0],
                               "model": identifier.split("_")[1], "generation_seconds": 0,
                               "graph_path": path.relative_to(tmp_path).as_posix()}
    payload = {"complete": True, "network_order": list(IDS), "results": results, "models": models}
    tables = tmp_path / "results/tables"
    write_csv(tables / "task2_global_properties.csv", TABLE_FIELDS, [results[key] for key in IDS])
    write_json(tables / "task2_global_properties.json", payload)
    write_csv(tables / "task2_model_parameters.csv", MODEL_FIELDS, list(models.values()))
    assert verify_outputs(tmp_path, graphs, context)["status"] == "PASS"
    payload["results"]["grqc_real"]["diameter"] = 999
    write_json(tables / "task2_global_properties.json", payload)
    with pytest.raises(ValueError, match="CSV/JSON disagreement"):
        verify_outputs(tmp_path, graphs, context)
