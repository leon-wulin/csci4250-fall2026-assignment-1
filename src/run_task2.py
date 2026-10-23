"""Run, checkpoint and verify Task 2 only. Run with conda environment fons-a1."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import networkx as nx

from scripts.inspect_datasets import graph_record
from src.task2_core import (
    TABLE_FIELDS, analyze_cached, cache_identity, digest_file, generate_models,
    graph_fingerprint, preprocess_graph, save_graph, validate_cache, validate_graph,
    write_csv, write_json, atomic_text,
)

IDS = ("grqc_real", "grqc_er", "grqc_ba", "power_real", "power_er", "power_ba")
MODEL_FIELDS = ("network_id", "family", "model", "n", "target_edges", "p", "m", "seed",
                "expected_edges", "generated_nodes", "generated_edges", "signed_edge_difference",
                "absolute_edge_difference", "relative_edge_difference", "signed_relative_edge_difference",
                "generation_seconds", "generator", "ba_initial_graph", "reference_graph_fingerprint")


def guard_environment() -> None:
    """Reject system/base Python even if the same dependencies are importable."""
    prefix = Path(sys.prefix).resolve()
    if (sys.version_info[:2] != (3, 12) or prefix.name.casefold() != "fons-a1"
            or Path(sys.executable).resolve().parent != prefix
            or Path(os.environ.get("CONDA_PREFIX", "")).resolve() != prefix):
        raise RuntimeError("Use conda run -n fons-a1 --no-capture-output python src/run_task2.py")


def protected_snapshot() -> dict[str, str]:
    """Include raw inputs, course sources and all official report source/output."""
    paths = [path for path in (ROOT / "data/raw").rglob("*") if path.is_file()]
    paths += [ROOT / "Assignment 1.docx", ROOT / "Assignment1_Fall2026_Network_Analysis_and_Visualization.pdf", ROOT / "AGENTS.md"]
    paths += list((ROOT / "report").glob("*.tex")) + list((ROOT / "report/sections").glob("*.tex"))
    paths += [ROOT / "report/report.pdf", ROOT / "report/README.md", ROOT / "report/build_report.ps1"]
    return {path.relative_to(ROOT).as_posix(): digest_file(path) for path in sorted(set(paths))}


def configure_log() -> logging.Logger:
    directory = ROOT / "results/logs"
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("task2")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s UTC %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    formatter.converter = time.gmtime
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(directory / "task2_execution.log", encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def publish(payload: dict) -> None:
    """Publish validated completed-network rows after each successful network."""
    tables = ROOT / "results/tables"
    write_csv(tables / "task2_global_properties.csv", TABLE_FIELDS, list(payload["results"].values()))
    write_json(tables / "task2_global_properties.json", payload)


def verify_outputs(root: Path, graphs: dict[str, nx.Graph], context: dict) -> dict:
    """Cross-check CSV/JSON, GraphML and node-level caches without repeating BFS."""
    tables = root / "results/tables"
    payload = json.loads((tables / "task2_global_properties.json").read_text(encoding="utf-8"))
    with (tables / "task2_global_properties.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not payload["complete"] or tuple(payload["network_order"]) != IDS or len(rows) != 6:
        raise ValueError("Missing/partial six-network outputs")
    if set(payload["results"]) != set(IDS) or tuple(row["network_id"] for row in rows) != IDS:
        raise ValueError("Incorrect network identifiers/order")
    for row in rows:
        identifier = row["network_id"]
        record = payload["results"][identifier]
        for field in TABLE_FIELDS:
            if row[field] != str(record[field]):
                raise ValueError(f"CSV/JSON disagreement: {identifier}.{field}")
        graph = graphs[identifier]
        saved_graph = nx.read_graphml(root / record["graph_path"], node_type=int)
        validate_graph(saved_graph)
        if graph_fingerprint(saved_graph) != graph_fingerprint(graph):
            raise ValueError(f"GraphML fingerprint mismatch for {identifier}")
        identity = cache_identity(graph, context)
        cached = validate_cache(root / "results/cache", identifier, graph, identity)
        for field in cached:
            if cached[field] != record[field]:
                raise ValueError(f"Cache/JSON disagreement: {identifier}.{field}")
    with (tables / "task2_model_parameters.csv").open(encoding="utf-8", newline="") as stream:
        models = list(csv.DictReader(stream))
    if len(models) != 4 or {row["network_id"] for row in models} != {"grqc_er", "grqc_ba", "power_er", "power_ba"}:
        raise ValueError("Expected exactly four model parameter rows")
    for row in models:
        expected = payload["models"][row["network_id"]]
        for field in MODEL_FIELDS:
            if row[field] != ("" if expected[field] is None else str(expected[field])):
                raise ValueError(f"Model CSV/JSON disagreement: {row['network_id']}.{field}")
        graph = graphs[row["network_id"]]
        if graph.number_of_edges() != expected["generated_edges"] or len(graph) != expected["generated_nodes"]:
            raise ValueError("Model graph/parameter size mismatch")
    return {"status": "PASS", "networks": 6, "models": 4,
            "checks": ["CSV equals JSON", "node-level eccentricities reproduce all distance summaries",
                       "GraphML IDs/isolates/topology preserved", "whole-graph degrees/components verified",
                       "all cache identities and artifact hashes valid", "model counts/deviations consistent"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="validate existing outputs and caches without computing BFS")
    args = parser.parse_args()
    guard_environment()
    logger = configure_log()
    started = perf_counter()
    before = protected_snapshot()
    try:
        logger.info("Task 2 START verify_only=%s; interpreter=%s; Python=%s", args.verify_only, sys.executable, platform.python_version())
        config = json.loads((ROOT / "task2_config.json").read_text(encoding="utf-8"))
        if config["seed"] != 42 or config["grqc_self_loops"] != "remove" or config["degree_variance_ddof"] != 0:
            raise ValueError("Configuration differs from approved Task 2 conventions")
        # Always test before touching assignment-scale models or distance calculations.
        tests = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
                               cwd=ROOT, capture_output=True, text=True)
        atomic_text(ROOT / "results/logs/task2_tests.txt", tests.stdout + tests.stderr)
        logger.info("Unit tests: %s", (tests.stdout + tests.stderr).strip())
        if tests.returncode:
            raise RuntimeError("Unit tests failed; full-network analysis stopped")
        audit_path = ROOT / "results/tables/task2_input_audit.json"
        if not args.verify_only:
            audit = subprocess.run([sys.executable, str(ROOT / "scripts/inspect_datasets.py"), "--output", str(audit_path)],
                                   cwd=ROOT, capture_output=True, text=True)
            if audit.returncode:
                logger.error("Input audit failed: %s %s", audit.stdout, audit.stderr)
                raise RuntimeError("Input audit failed; stop before analysis")
        audited = json.loads(audit_path.read_text(encoding="utf-8"))
        baseline = json.loads((ROOT / "results/tables/dataset_preflight.json").read_text(encoding="utf-8"))
        for entry in baseline["protected_files"]:
            if digest_file(ROOT / entry["path"]) != entry["sha256"]:
                raise ValueError(f"Input differs from previously validated baseline: {entry['path']}")
        for entry in audited["protected_files"]:
            if digest_file(ROOT / entry["path"]) != entry["sha256"]:
                raise ValueError("Source changed after input audit")
        for warning in audited["warnings"]:
            logger.warning("Input audit (historical raw semantics): %s", warning)
        context = {
            "config": config, "versions": {name: version(name) for name in ("networkx", "numpy", "pandas", "scipy", "pytest")},
            "python": platform.python_version(),
            "source_hashes": {entry["path"]: entry["sha256"] for entry in audited["protected_files"]},
            "code_sha256": {path.relative_to(ROOT).as_posix(): digest_file(path)
                            for path in (ROOT / "src/task2_core.py", ROOT / "src/run_task2.py", ROOT / "scripts/inspect_datasets.py")},
        }
        graphs, preprocessing, models, generation = {}, {}, {}, {}
        for family, audit_key in (("grqc", "ca_grqc"), ("power", "power")):
            evidence = audited["datasets"][audit_key]
            path = ROOT / evidence["file"]
            raw = (nx.read_edgelist(path, nodetype=int, data=False, create_using=nx.Graph)
                   if family == "grqc" else nx.read_gml(path, label=None))
            current = graph_record(raw)
            for key in ("nodes", "edges", "self_loops", "components", "lcc_nodes", "directed", "weighted"):
                if current[key] != evidence[key]:
                    raise ValueError(f"Loaded {family} disagrees with input audit: {key}")
            graph, changes = preprocess_graph(raw, remove_self_loops=(family == "grqc"))
            if (len(graph), graph.number_of_edges()) != ((5242, 14484) if family == "grqc" else (4941, 6594)):
                raise ValueError("Analyzed size differs from explicitly approved transformation")
            graphs[f"{family}_real"] = graph
            generation[f"{family}_real"] = 0.0
            preprocessing[family] = {**changes, "raw_audit": evidence}
            logger.info("%s raw N=%d M=%d -> analyzed N=%d M=%d; removed loops=%d; no nodes removed", family,
                        len(raw), raw.number_of_edges(), len(graph), graph.number_of_edges(), changes["removed_self_loops"])
            for identifier, generated, parameters in generate_models(graph, family=family, seed=config["seed"]):
                graphs[identifier] = generated
                parameters["reference_graph_fingerprint"] = graph_fingerprint(graph)
                models[identifier] = parameters
                generation[identifier] = parameters["generation_seconds"]
                logger.info("%s seed=42 p=%s m=%s actual M=%d delta=%+d (%.6f%% absolute)", identifier,
                            parameters["p"], parameters["m"], parameters["generated_edges"],
                            parameters["signed_edge_difference"], 100 * parameters["relative_edge_difference"])
        logger.warning("Power BA m=1 yields a tree with 4940 edges vs 6594 target: structural density mismatch, not an implementation defect")
        logger.info("ca-GrQc ER uses the approved loop-free M=14484, not the original M=14496")
        if args.verify_only:
            verification = verify_outputs(ROOT, graphs, context)
            if before != protected_snapshot():
                raise ValueError("Protected inputs/report changed during verification")
            logger.info("VERIFY ONLY PASS: %s; elapsed %.6f s", verification, perf_counter() - started)
            return 0
        write_csv(ROOT / "results/tables/task2_model_parameters.csv", MODEL_FIELDS, list(models.values()))
        write_json(ROOT / "results/tables/task2_preprocessing.json", preprocessing)
        payload = {
            "complete": False, "network_order": list(IDS), "results": {}, "models": models,
            "preprocessing": preprocessing, "cache_context": context,
            "metadata": {"started_utc": datetime.now(timezone.utc).isoformat(), "executable": sys.executable,
                         "seed_policy": "one sample per model; seed=42 for all four; supersedes old planned seeds",
                         "degree_scope": "whole analyzed graph", "variance_ddof": 0,
                         "distance_scope": "largest connected component", "distance_unit": "hops",
                         "average_eccentricity_is_not_average_shortest_path_length": True,
                         "timing_definition": "analysis_seconds includes exact BFS and metric validation, excludes generation/I/O; cached runs retain original analysis timings",
                         "unit_tests": tests.stdout.strip(), "protected_files_before": before},
        }
        publish(payload)
        for identifier in IDS:
            graph = graphs[identifier]
            graph_path = ROOT / f"data/processed/task2/{identifier}.graphml"
            save_graph(graph_path, graph)
            result, reused = analyze_cached(graph, identifier, ROOT / "results/cache", context, logger)
            payload["results"][identifier] = {
                **result, "network_id": identifier, "family": identifier.split("_")[0], "model": identifier.split("_")[1],
                "generation_seconds": generation[identifier], "cache_reused_this_run": reused,
                "graph_path": graph_path.relative_to(ROOT).as_posix(), "graphml_sha256": digest_file(graph_path),
                "eccentricity_path": f"results/cache/eccentricity_{identifier}.csv",
            }
            publish(payload)
        if before != protected_snapshot():
            raise ValueError("Protected input or report changed during computation")
        payload["complete"] = True
        payload["metadata"].update(protected_files_unchanged=True, elapsed_seconds=perf_counter() - started,
                                    completed_utc=datetime.now(timezone.utc).isoformat())
        publish(payload)
        try:
            verification = verify_outputs(ROOT, graphs, context)
        except Exception:
            payload["complete"] = False
            publish(payload)
            raise
        payload["verification"] = verification
        publish(payload)
        write_json(ROOT / "results/tables/task2_verification.json", verification)
        logger.info("Task 2 COMPLETE: six networks validated; wall time %.6f s; raw data/LaTeX unchanged", perf_counter() - started)
        return 0
    except Exception:
        logger.exception("Task 2 FAILED; do not treat incomplete output as final")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
