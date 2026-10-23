"""Frozen Task 2 inputs and zero-preserving Task 3 empirical distributions."""
from __future__ import annotations

import csv
import json
import math
from importlib.metadata import version
from pathlib import Path

import networkx as nx
import numpy as np

from src.run_task2 import IDS, verify_outputs
from src.task2_core import cache_identity, digest_file, graph_fingerprint, validate_cache

METRICS = ("degree", "eccentricity", "clustering", "component_size")
SCOPES = {"degree": "all nodes", "eccentricity": "LCC nodes",
          "clustering": "all nodes", "component_size": "one observation per component"}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_frozen_task2(root: Path) -> tuple[dict, dict[str, nx.Graph]]:
    """Verify saved versions/configuration/topology/caches without random generation or BFS."""
    payload = json.loads((root / "results/tables/task2_global_properties.json").read_text(encoding="utf-8"))
    if not payload.get("complete") or tuple(payload["network_order"]) != IDS:
        raise ValueError("Task 2 six-network results must be complete")
    context = payload["cache_context"]
    if json.loads((root / "task2_config.json").read_text()) != context["config"]:
        raise ValueError("Task 2 configuration changed")
    for package, expected in context["versions"].items():
        if version(package) != expected:
            raise ValueError(f"Task 2 environment changed: {package}")
    for relative, expected in {**context["code_sha256"], **context["source_hashes"]}.items():
        if digest_file(root / relative) != expected:
            raise ValueError(f"Task 2 source/code identity changed: {relative}")
    graphs = {}
    for identifier in IDS:
        result = payload["results"][identifier]
        path = root / result["graph_path"]
        if digest_file(path) != result["graphml_sha256"]:
            raise ValueError(f"GraphML file changed: {identifier}")
        graph = nx.read_graphml(path, node_type=int)
        if (len(graph), graph.number_of_edges(), graph_fingerprint(graph)) != (
                result["number_of_nodes"], result["number_of_edges"], result["graph_fingerprint"]):
            raise ValueError(f"Task 2 topology changed: {identifier}")
        validate_cache(root / "results/cache", identifier, graph, cache_identity(graph, context))
        graphs[identifier] = graph
    verify_outputs(root, graphs, context)
    for identifier, params in payload["models"].items():
        real = graphs[params["family"] + "_real"]
        n, m = len(real), real.number_of_edges()
        if params["seed"] != 42 or params["n"] != n or params["target_edges"] != m:
            raise ValueError("Model seed/reference size changed")
        if params["reference_graph_fingerprint"] != graph_fingerprint(real):
            raise ValueError("Model reference graph changed")
        if params["model"] == "er" and params["p"] != 2 * m / (n * (n - 1)):
            raise ValueError("ER p no longer matches the approved analyzed graph")
        if params["model"] == "ba" and params["generated_edges"] != params["m"] * (n - params["m"]):
            raise ValueError("BA edge formula failed")
    return payload, graphs


def collect_samples(root: Path, identifier: str, graph: nx.Graph) -> tuple[dict[str, np.ndarray], dict[str, list[int]]]:
    """Reuse degree/components/eccentricity; compute local clustering over every node."""
    cache = root / "results/cache"
    degrees = read_csv(cache / f"degrees_{identifier}.csv")
    ecc = read_csv(cache / f"eccentricity_{identifier}.csv")
    components = read_csv(cache / f"components_{identifier}.csv")
    nodes = sorted(graph)
    clustering = nx.clustering(graph, nodes=nodes)
    samples = {
        "degree": np.array([int(row["degree"]) for row in degrees], dtype=np.int64),
        "eccentricity": np.array([int(row["eccentricity"]) for row in ecc], dtype=np.int64),
        "clustering": np.array([clustering[node] for node in nodes], dtype=np.float64),
        "component_size": np.array([int(row["size"]) for row in components], dtype=np.int64),
    }
    identifiers = {
        "degree": [int(row["node_id"]) for row in degrees],
        "eccentricity": [int(row["node_id"]) for row in ecc], "clustering": nodes,
        "component_size": [int(row["component_id"]) for row in components],
    }
    return samples, identifiers


def statistics(samples: np.ndarray) -> dict:
    """Keep all observations; reported variance is population variance."""
    values = np.asarray(samples)
    if values.ndim != 1 or len(values) == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Expected finite nonempty one-dimensional samples")
    return {"n_samples": len(values), "mean": float(values.mean()),
            "population_variance": float(values.var(ddof=0)),
            "minimum": float(values.min()), "maximum": float(values.max()),
            "zero_count": int(np.count_nonzero(values == 0)), "one_count": int(np.count_nonzero(values == 1))}


def empirical_frequencies(samples: np.ndarray, metric: str) -> list[dict]:
    """Dense integer PMFs (including empty bins); exact-value masses for clustering."""
    values = np.asarray(samples)
    if metric == "clustering":
        x, counts = np.unique(values, return_counts=True)
    else:
        if np.any(values != np.floor(values)) or np.any(values < 0) or (metric == "component_size" and np.any(values < 1)):
            raise ValueError("Expected nonnegative integer observations; component sizes are positive")
        start = 1 if metric == "component_size" else 0
        x = np.arange(start, int(values.max()) + 1)
        counts = np.bincount(values.astype(int), minlength=int(values.max()) + 1)[start:]
    return [{"value": float(value), "count": int(count), "probability": float(count / len(values))}
            for value, count in zip(x, counts)]


def clustering_bins(samples: np.ndarray, n_bins: int = 20) -> list[dict]:
    """Keep exact zero/one atoms separate from interior bins normalized by all nodes."""
    values = np.asarray(samples)
    if np.any((values < 0) | (values > 1)) or not np.all(np.isfinite(values)):
        raise ValueError("Clustering must lie in [0,1]")
    interior = values[(values > 0) & (values < 1)]
    counts, edges = np.histogram(interior, bins=np.linspace(0, 1, n_bins + 1))
    rows = [{"kind": "zero_atom", "left": 0.0, "right": 0.0, "value": 0.0,
             "count": int(np.count_nonzero(values == 0))}]
    rows += [{"kind": "interior_bin", "left": float(left), "right": float(right),
              "value": float((left + right) / 2), "count": int(count)}
             for left, right, count in zip(edges[:-1], edges[1:], counts)]
    rows += [{"kind": "one_atom", "left": 1.0, "right": 1.0, "value": 1.0,
              "count": int(np.count_nonzero(values == 1))}]
    for row in rows:
        row["probability"] = row["count"] / len(values)
    if sum(row["count"] for row in rows) != len(values):
        raise ValueError("Clustering histogram lost observations")
    return rows


def validate_samples(identifier: str, graph: nx.Graph, samples: dict[str, np.ndarray], task2: dict) -> None:
    """Numerical and scope checks independent of plotting and fitting."""
    for values in samples.values():
        statistics(values)
    degree, ecc, clustering, sizes = (samples[name] for name in METRICS)
    if len(degree) != len(graph) or len(clustering) != len(graph) or degree.sum() != 2 * graph.number_of_edges():
        raise ValueError("Whole-node degree/clustering scope invariant failed")
    if len(sizes) != task2["number_of_components"] or sizes.sum() != len(graph):
        raise ValueError("Component sample weighting/count invariant failed")
    if len(ecc) != task2["lcc_size"] or ecc.min() != task2["radius"] or ecc.max() != task2["diameter"]:
        raise ValueError("Eccentricity cache/LCC mismatch")
    if not math.isclose(ecc.mean(), task2["average_eccentricity"], rel_tol=1e-13):
        raise ValueError("Eccentricity mean differs from Task 2")
    if not math.isclose(degree.mean(), task2["average_degree"], rel_tol=1e-13) or not math.isclose(degree.var(), task2["degree_variance"], rel_tol=1e-13):
        raise ValueError("Degree moments differ from Task 2")
    if np.any((clustering < 0) | (clustering > 1)) or np.any(clustering[degree < 2] != 0):
        raise ValueError("Clustering range/low-degree-zero convention failed")
    if identifier == "power_ba" and np.any(clustering != 0):
        raise ValueError("Power BA tree must have all-zero clustering")
    if len(sizes) == 1 and sizes.var() != 0:
        raise ValueError("A one-component graph must have zero component-size variance")
    for metric, values in samples.items():
        freq = empirical_frequencies(values, metric)
        if sum(row["count"] for row in freq) != len(values) or not math.isclose(sum(row["probability"] for row in freq), 1.0):
            raise ValueError(f"Frequency normalization failed: {metric}")
