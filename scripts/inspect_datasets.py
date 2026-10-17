"""Audit local inputs read-only; never compute full-network distance metrics."""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import zipfile
from collections import Counter
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
PLANNED_SEEDS = {
    "ca_grqc_er": 2026101701, "ca_grqc_ba": 2026101702,
    "power_er": 2026101703, "power_ba": 2026101704,
}


def file_record(path: Path) -> dict:
    """Return a content identity without changing the input."""
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()).hexdigest()}


def nearest_ba_parameter(n: int, edges: int) -> int:
    """Break symmetric integer-m edge-count ties by choosing the smaller m."""
    return min(range(1, n), key=lambda m: (abs(m * (n - m) - edges), m))


def planned_parameters(n: int, edges: int) -> dict:
    """Compute parameters arithmetically, without generating an assignment graph."""
    m = nearest_ba_parameter(n, edges)
    return {"status": "planned; no assignment random graph generated", "n": n,
            "reference_m": edges, "er_p": 2 * edges / (n * (n - 1)),
            "er_expected_edges": edges, "ba_m": m,
            "ba_formula_edges": m * (n - m),
            "ba_edge_difference": m * (n - m) - edges}


def graph_record(graph: nx.Graph) -> dict:
    """Compute only the inexpensive input-readiness properties requested."""
    components = list(nx.connected_components(graph))
    if sum(degree for _, degree in graph.degree()) != 2 * graph.number_of_edges():
        raise ValueError("Undirected degree-sum invariant failed")
    return {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(),
            "graph_type": type(graph).__name__, "directed": graph.is_directed(),
            "multigraph": graph.is_multigraph(), "weighted": nx.is_weighted(graph),
            "self_loops": nx.number_of_selfloops(graph),
            "self_loop_nodes": sorted(node for node, _ in nx.selfloop_edges(graph)),
            "isolates": nx.number_of_isolates(graph), "components": len(components),
            "lcc_nodes": max(map(len, components)),
            "edge_attribute_keys": sorted({key for _, _, attrs in graph.edges(data=True) for key in attrs})}


def edge_record(records: list[tuple[int, int]]) -> dict:
    """Distinguish exact repeated lines from reciprocal undirected records."""
    ordered = Counter(records)
    unordered = Counter(tuple(sorted(pair)) for pair in records)
    return {"raw_records": len(records), "unique_ordered_pairs": len(ordered),
            "exact_duplicate_records": len(records) - len(ordered),
            "unique_unordered_pairs": len(unordered),
            "unordered_duplicate_records": len(records) - len(unordered),
            "reciprocal_nonloop_pairs": sum(
                1 for u, v in unordered if u != v and (u, v) in ordered and (v, u) in ordered),
            "asymmetric_nonloop_pairs": sum(
                1 for u, v in unordered if u != v and not ((u, v) in ordered and (v, u) in ordered))}


def unique_input(filename: str) -> Path:
    matches = [path for path in (ROOT / "data/raw").rglob("*")
               if path.is_file() and path.name.casefold() == filename.casefold()]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one local {filename}; found {matches}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/tables/dataset_preflight.json")
    args = parser.parse_args()
    args.output = args.output.resolve()
    tables = (ROOT / "results/tables").resolve()
    if not args.output.is_relative_to(tables) or args.output == tables:
        parser.error("Audit output must be a file under results/tables; source inputs are read-only")
    prefix = Path(sys.prefix).resolve()
    if (sys.version_info[:2] != (3, 12) or prefix.name.casefold() != "fons-a1"
        or Path(sys.executable).resolve().parent != prefix
        or Path(os.environ.get("CONDA_PREFIX", "")).resolve() != prefix):
        parser.error("Use conda run -n fons-a1 --no-capture-output python")
    grqc_path, power_path = unique_input("CA-GrQc.txt"), unique_input("power.gml")
    protected = sorted(path for path in (ROOT / "data/raw").rglob("*") if path.is_file())
    protected += [ROOT / "Assignment 1.docx", ROOT / "Assignment1_Fall2026_Network_Analysis_and_Visualization.pdf"]
    before = [file_record(path) for path in protected]
    text = grqc_path.read_text(encoding="utf-8")
    comments, records = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            comments.append(line)
            continue
        fields = line.split()
        if len(fields) != 2:
            raise ValueError(f"Malformed ca-GrQc record at line {number}")
        records.append(tuple(map(int, fields)))
    grqc = nx.read_edgelist(grqc_path, nodetype=int, data=False, create_using=nx.Graph)
    grqc_metadata = {"file": grqc_path.relative_to(ROOT).as_posix(), "format": "UTF-8 two-column edge list",
                     "header": comments, "malformed_records": 0,
                     **edge_record(records), **graph_record(grqc)}
    if (grqc.number_of_nodes(), grqc.number_of_edges()) != (5242, 14496):
        raise ValueError("ca-GrQc loaded size differs from the documented specification")

    power_text = power_path.read_text(encoding="ascii")
    blocks = re.findall(r"\bedge\s*\[([^\[\]]*)\]", power_text)
    if len(blocks) != len(re.findall(r"^\s*edge\s*\[", power_text, flags=re.MULTILINE)):
        raise ValueError("Unexpected nested GML edges; inspect before proceeding")
    power_records = []
    for block in blocks:
        source = re.findall(r"\bsource\s+(\d+)", block)
        target = re.findall(r"\btarget\s+(\d+)", block)
        if len(source) != 1 or len(target) != 1:
            raise ValueError("Unexpected GML source/target fields")
        power_records.append((int(source[0]), int(target[0])))
    power = nx.read_gml(power_path, label=None)
    power_metadata = {"file": power_path.relative_to(ROOT).as_posix(), "format": "ASCII GML",
                      "node_handling": "label=None preserves explicitly declared numeric node IDs, including isolates",
                      "orientation_note": "GML declares directed 0; one source/target record per undirected edge is expected, not a directionality discrepancy",
                      **edge_record(power_records), **graph_record(power)}
    if (power.number_of_nodes(), power.number_of_edges()) != (4941, 6594):
        raise ValueError("Power Grid loaded size differs from the documented specification")
    if len(power_records) != power.number_of_edges():
        raise ValueError("Raw GML record count differs from loaded edge count")

    archive_results = []
    for path in protected:
        if path.suffix.casefold() == ".zip":
            with zipfile.ZipFile(path) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise ValueError(f"Corrupt ZIP member: {bad_member}")
            archive_results.append({"path": str(path.relative_to(ROOT)), "integrity": "PASS"})
        elif path.suffix.casefold() == ".gz":
            with gzip.open(path, "rb") as archive:
                while archive.read(1024 * 1024):
                    pass
            archive_results.append({"path": str(path.relative_to(ROOT)), "integrity": "PASS"})
    after = [file_record(path) for path in protected]
    if before != after:
        raise ValueError("A protected source file changed during the audit")
    report = {
        "scope": "Input readiness only; no full-network distances, clustering, random models or distributions",
        "python": sys.version, "executable": sys.executable,
        "versions": {name: version(name) for name in ("networkx", "numpy", "pandas", "matplotlib", "scipy", "pytest")},
        "protected_files": after, "protected_hashes_unchanged": True,
        "archive_checks": archive_results,
        "archive_note": "No dataset archives present; original download CRC/integrity cannot be verified" if not archive_results else "Archives checked",
        "datasets": {"ca_grqc": grqc_metadata, "power": power_metadata},
        "planned_seeds": PLANNED_SEEDS,
        "planned_models": {
            "ca_grqc_as_loaded_including_12_loops": planned_parameters(5242, 14496),
            "ca_grqc_proposed_loop_free_not_created": planned_parameters(5242, 14484),
            "power": planned_parameters(4941, 6594),
        },
        "warnings": [
            "ca-GrQc header says directed but all nonloop pairs are reciprocal; Graph explicitly combines reverse records",
            "ca-GrQc includes 12 self-loops; raw Graph retains all 12. Loop-free preprocessing policy must be explicit before analysis",
            "Edge-list files cannot declare isolates; no nodes were synthesized or removed to match metadata",
            "Download timestamps and upstream checksum verification remain unavailable; local hashes establish identity, not upstream authenticity",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
