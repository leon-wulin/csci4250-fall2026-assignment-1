"""Exact Task 2 statistics, validated artifacts and configuration-aware caches."""
from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import tempfile
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Callable

import networkx as nx
import numpy as np

from scripts.inspect_datasets import nearest_ba_parameter

ALGORITHM = "task2-exact-bfs-v1"
METRIC_FIELDS = (
    "number_of_nodes", "number_of_edges", "number_of_components", "lcc_size",
    "diameter", "radius", "average_eccentricity", "average_degree", "degree_variance",
)
TABLE_FIELDS = ("network_id", "family", "model", *METRIC_FIELDS,
                "self_loops", "isolates", "degree_sum", "analysis_seconds",
                "eccentricity_seconds", "generation_seconds", "graph_fingerprint")


def digest_file(path: Path) -> str:
    """Hash an existing artifact without changing it."""
    return sha256(path.read_bytes()).hexdigest()


def canonical_json(value: object) -> str:
    """Serialize JSON deterministically and reject nonfinite values."""
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def atomic_text(path: Path, content: str) -> None:
    """Publish a complete UTF-8 artifact with a same-directory atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.stem + "-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path: Path, value: object) -> None:
    atomic_text(path, canonical_json(value))


def write_csv(path: Path, fields: tuple | list, rows: list[dict]) -> None:
    """Keep Python's round-trip float precision rather than report rounding."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    atomic_text(path, output.getvalue())


def validate_graph(graph: nx.Graph, *, allow_loops: bool = False) -> None:
    """Accept nonempty, integer-ID, undirected, unweighted topology only."""
    if graph.is_directed() or graph.is_multigraph() or not graph:
        raise ValueError("Expected a nonempty undirected Graph, not a directed/multigraph")
    if any(not isinstance(node, int) or isinstance(node, bool) for node in graph):
        raise ValueError("Task 2 node IDs must be integers")
    if any("weight" in attrs for _, _, attrs in graph.edges(data=True)):
        raise ValueError("Weighted inputs require an explicit approved conversion")
    if not allow_loops and nx.number_of_selfloops(graph):
        raise ValueError("Unexpected self-loops in the analyzed graph")


def graph_fingerprint(graph: nx.Graph) -> str:
    """Include every node (including isolates) and canonical undirected edges."""
    nodes = sorted(graph)
    edges = sorted((min(u, v), max(u, v)) for u, v in graph.edges)
    return sha256(canonical_json({"nodes": nodes, "edges": edges}).encode()).hexdigest()


def preprocess_graph(raw: nx.Graph, *, remove_self_loops: bool) -> tuple[nx.Graph, dict]:
    """Copy topology, explicitly remove approved loops, and retain all nodes."""
    validate_graph(raw, allow_loops=True)
    result = nx.Graph()
    result.add_nodes_from(sorted(raw))
    result.add_edges_from(sorted((min(u, v), max(u, v)) for u, v in raw.edges))
    loops = sorted(u for u, _ in nx.selfloop_edges(raw))
    if loops and not remove_self_loops:
        raise ValueError("Loop policy not approved: refuse an implicit transformation")
    result.remove_edges_from((node, node) for node in loops)
    validate_graph(result)
    if set(result) != set(raw) or result.number_of_edges() != raw.number_of_edges() - len(loops):
        raise ValueError("Preprocessing node/edge preservation failed")
    return result, {
        "original_nodes": len(raw), "original_edges": raw.number_of_edges(),
        "analyzed_nodes": len(result), "analyzed_edges": result.number_of_edges(),
        "removed_self_loop_nodes": loops, "removed_self_loops": len(loops),
        "removed_nodes": 0, "policy": "remove self-loops in derived copy; retain all nodes",
        "attribute_policy": "topology-only export; preserve numeric node IDs; no weights added",
    }


def generate_models(real: nx.Graph, *, family: str, seed: int = 42) -> list[tuple[str, nx.Graph, dict]]:
    """Generate one G(n,p) and standard default-star BA sample, without retries."""
    validate_graph(real)
    n, target = len(real), real.number_of_edges()
    if n < 2 or target == 0:
        raise ValueError("Model comparison requires n>=2 and positive target edges")
    p = 2 * target / (n * (n - 1))
    m = nearest_ba_parameter(n, target)
    output = []
    for model in ("er", "ba"):
        start = perf_counter()
        graph = (nx.gnp_random_graph(n, p, seed=seed) if model == "er"
                 else nx.barabasi_albert_graph(n, m, seed=seed))
        seconds = perf_counter() - start
        validate_graph(graph)
        actual = graph.number_of_edges()
        if len(graph) != n or (model == "ba" and actual != m * (n - m)):
            raise ValueError("Generated graph violates node count or BA edge formula")
        delta = actual - target
        metadata = {
            "network_id": f"{family}_{model}", "family": family, "model": model,
            "n": n, "target_edges": target, "seed": seed,
            "p": p if model == "er" else None, "m": m if model == "ba" else None,
            "expected_edges": target if model == "er" else m * (n - m),
            "generated_nodes": len(graph), "generated_edges": actual,
            "signed_edge_difference": delta, "absolute_edge_difference": abs(delta),
            "relative_edge_difference": abs(delta) / target,
            "signed_relative_edge_difference": delta / target,
            "generation_seconds": seconds, "generator": "gnp_random_graph" if model == "er" else "barabasi_albert_graph",
            "ba_initial_graph": "NetworkX default star on m+1 nodes" if model == "ba" else None,
            "node_mapping": "generated model IDs are integers 0..n-1, not author/facility IDs",
        }
        output.append((metadata["network_id"], graph, metadata))
    return output


def topology(graph: nx.Graph) -> tuple[list[set[int]], list[int], nx.Graph]:
    """Choose LCC deterministically: largest size, then smallest numeric node ID."""
    validate_graph(graph)
    components = sorted(nx.connected_components(graph), key=lambda c: (-len(c), min(c)))
    nodes = sorted(components[0])
    return components, nodes, graph.subgraph(nodes)


def summarize(graph: nx.Graph, eccentricities: dict[int, int]) -> dict:
    """Validate cached/node-level data and derive all nine metrics without BFS."""
    components, lcc_nodes, lcc = topology(graph)
    if set(eccentricities) != set(lcc_nodes):
        raise ValueError("Eccentricity node IDs must equal the entire LCC")
    if any(type(value) is not int or not 0 <= value < len(lcc) for value in eccentricities.values()):
        raise ValueError("Invalid eccentricity values")
    if len(lcc) > 1 and min(eccentricities.values()) < 1:
        raise ValueError("Nontrivial connected graph cannot have eccentricity zero")
    if any(abs(eccentricities[u] - eccentricities[v]) > 1 for u, v in lcc.edges):
        raise ValueError("Adjacent-node eccentricity invariant failed")
    degrees = np.array([degree for _, degree in graph.degree()], dtype=np.int64)
    ecc = np.array(list(eccentricities.values()), dtype=np.int64)
    result = {
        "number_of_nodes": len(graph), "number_of_edges": graph.number_of_edges(),
        "number_of_components": len(components), "lcc_size": len(lcc_nodes),
        "diameter": int(ecc.max()), "radius": int(ecc.min()),
        "average_eccentricity": float(ecc.mean()), "average_degree": float(degrees.mean()),
        "degree_variance": float(degrees.var(ddof=0)), "degree_sum": int(degrees.sum()),
        "self_loops": nx.number_of_selfloops(graph), "isolates": nx.number_of_isolates(graph),
    }
    n, edges = result["number_of_nodes"], result["number_of_edges"]
    if sum(map(len, components)) != n or not 1 <= len(lcc_nodes) <= n:
        raise ValueError("Whole-graph component invariants failed")
    if result["degree_sum"] != 2 * edges or not math.isclose(result["average_degree"], 2 * edges / n):
        raise ValueError("Whole-graph degree invariants failed")
    if not result["radius"] <= result["average_eccentricity"] <= result["diameter"] <= 2 * result["radius"]:
        raise ValueError("Distance bounds failed")
    if not all(math.isfinite(value) for value in result.values()) or result["degree_variance"] < 0:
        raise ValueError("Nonfinite/negative statistics")
    return result


def calculate_global_properties(graph: nx.Graph, progress: Callable[[int, int], None] | None = None) -> tuple[dict, dict[int, int]]:
    """Run exactly one unweighted BFS per LCC node; do not retain all-pairs distances."""
    start = perf_counter()
    _, nodes, lcc_view = topology(graph)
    lcc = nx.Graph(lcc_view)  # Avoid repeated subgraph-view filtering in every BFS.
    eccentricities = {}
    bfs_start = perf_counter()
    for index, node in enumerate(nodes, 1):
        distances = nx.single_source_shortest_path_length(lcc, node)
        if len(distances) != len(nodes):
            raise ValueError("BFS did not reach every LCC node")
        eccentricities[node] = max(distances.values())
        if progress is not None and (index % 250 == 0 or index == len(nodes)):
            progress(index, len(nodes))
    bfs_seconds = perf_counter() - bfs_start
    result = summarize(graph, eccentricities)
    result.update(analysis_seconds=perf_counter() - start, eccentricity_seconds=bfs_seconds)
    return result, eccentricities


def save_graph(path: Path, graph: nx.Graph) -> None:
    """Round-trip GraphML, explicitly preserving isolates and integer identifiers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".graphml.tmp")
    nx.write_graphml(graph, temporary, prettyprint=False)
    restored = nx.read_graphml(temporary, node_type=int)
    validate_graph(restored)
    if graph_fingerprint(restored) != graph_fingerprint(graph):
        raise ValueError("GraphML round-trip changed graph topology/identifiers")
    os.replace(temporary, path)


def cache_identity(graph: nx.Graph, context: dict) -> dict:
    return {"algorithm": ALGORITHM, "graph_fingerprint": graph_fingerprint(graph), "context": context}


def cache_paths(directory: Path, network_id: str) -> dict[str, Path]:
    return {"eccentricity": directory / f"eccentricity_{network_id}.csv",
            "degrees": directory / f"degrees_{network_id}.csv",
            "components": directory / f"components_{network_id}.csv",
            "manifest": directory / f"task2_{network_id}.json"}


def validate_cache(directory: Path, network_id: str, graph: nx.Graph, identity: dict) -> dict:
    """Reject incomplete, stale or corrupted caches before trusting their values."""
    paths = cache_paths(directory, network_id)
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    if not manifest.get("complete") or manifest["identity"] != identity:
        raise ValueError("Incomplete or stale cache")
    for name in ("eccentricity", "degrees", "components"):
        if digest_file(paths[name]) != manifest["sha256"][name]:
            raise ValueError(f"Corrupted {name} cache for {network_id}")
    with paths["eccentricity"].open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    ecc = {int(row["node_id"]): int(row["eccentricity"]) for row in rows}
    if len(ecc) != len(rows) or any(row["network_id"] != network_id for row in rows):
        raise ValueError("Duplicate node IDs or incorrect eccentricity network ID")
    with paths["degrees"].open(encoding="utf-8", newline="") as stream:
        degrees = list(csv.DictReader(stream))
    if [(int(row["node_id"]), int(row["degree"])) for row in degrees] != sorted(graph.degree()):
        raise ValueError("Cached degrees differ from full graph")
    with paths["components"].open(encoding="utf-8", newline="") as stream:
        sizes = list(csv.DictReader(stream))
    components, _, _ = topology(graph)
    expected_sizes = [(index, len(nodes), min(nodes)) for index, nodes in enumerate(components)]
    if [(int(row["component_id"]), int(row["size"]), int(row["smallest_node_id"])) for row in sizes] != expected_sizes:
        raise ValueError("Cached component sizes differ from full graph")
    derived = summarize(graph, ecc)
    for key, value in derived.items():
        if not math.isclose(manifest["result"][key], value, rel_tol=1e-13, abs_tol=1e-13):
            raise ValueError(f"Cache/summary mismatch: {network_id}.{key}")
    return manifest["result"]


def analyze_cached(graph: nx.Graph, network_id: str, directory: Path, context: dict, logger: logging.Logger) -> tuple[dict, bool]:
    """Commit each finished network independently; manifest is written last."""
    paths = cache_paths(directory, network_id)
    identity = cache_identity(graph, context)
    if paths["manifest"].exists():
        previous = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        if previous.get("identity") == identity and previous.get("complete"):
            result = validate_cache(directory, network_id, graph, identity)
            logger.info("%s cache HIT: validated complete artifacts; no BFS", network_id)
            return result, True
        logger.warning("%s cache INVALIDATED: graph/configuration/code/versions changed", network_id)
    logger.info("%s exact BFS analysis START: N=%d M=%d", network_id, len(graph), graph.number_of_edges())
    result, ecc = calculate_global_properties(
        graph, lambda done, total: logger.info("%s BFS %d/%d", network_id, done, total))
    result["graph_fingerprint"] = identity["graph_fingerprint"]
    write_csv(paths["eccentricity"], ("network_id", "node_id", "eccentricity"),
              [{"network_id": network_id, "node_id": node, "eccentricity": ecc[node]} for node in sorted(ecc)])
    write_csv(paths["degrees"], ("node_id", "degree"),
              [{"node_id": node, "degree": degree} for node, degree in sorted(graph.degree())])
    components, _, _ = topology(graph)
    write_csv(paths["components"], ("component_id", "size", "smallest_node_id"),
              [{"component_id": i, "size": len(nodes), "smallest_node_id": min(nodes)} for i, nodes in enumerate(components)])
    write_json(paths["manifest"], {"complete": True, "identity": identity, "result": result,
               "sha256": {name: digest_file(paths[name]) for name in ("eccentricity", "degrees", "components")}})
    validate_cache(directory, network_id, graph, identity)
    logger.info("%s PASS: exact metrics/cache verified; analysis %.6f s; BFS %.6f s", network_id, result["analysis_seconds"], result["eccentricity_seconds"])
    return result, False
