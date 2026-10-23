"""Compute/plot Task 3 from frozen Task 2 graphs and caches; never edit reports."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from importlib.metadata import version
import json
import logging
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "results/cache/task3_mpl"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import networkx as nx
import numpy as np
from PIL import Image
from src.run_task2 import IDS, guard_environment, protected_snapshot
from src.task2_core import digest_file, write_csv, write_json, atomic_text
from src.task3_distributions import (METRICS, SCOPES, read_csv, load_frozen_task2,
    collect_samples, statistics, empirical_frequencies, clustering_bins, validate_samples)
from src.task3_fitting import fit_distribution, curve_rows
from src.task3_plotting import render_composite

STAT_FIELDS = ("network_id", "metric", "scope", "n_samples", "mean", "population_variance", "minimum", "maximum", "zero_count", "one_count")
FIT_FIELDS = ("network_id", "metric", "status", "method", "fit_scope", "n_fit", "scope_weight", "ks", "aic", "reason", "parameters_json", "candidates_json")


def configure_log() -> logging.Logger:
    (ROOT / "results/logs").mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("task3")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s UTC %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    formatter.converter = time.gmtime
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(ROOT / "results/logs/task3_execution.log", encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def input_snapshot(root: Path) -> dict:
    result = protected_snapshot()
    inventory = json.loads((root / "results/tables/task2_artifact_manifest.json").read_text(encoding="utf-8"))
    for row in inventory["outputs"]:
        current = digest_file(root / row["path"])
        if current != row["sha256"]:
            raise ValueError(f"Frozen Task 2 artifact changed: {row['path']}")
        result[row["path"]] = current
    for relative in ("task2_config.json", "src/task2_core.py", "src/run_task2.py", "tests/test_task2.py"):
        result[relative] = digest_file(root / relative)
    return result


def identity(root: Path, config: dict, before: dict) -> dict:
    return {"schema": "task3-v1", "config": config, "protected_inputs": before,
            "versions": {name: version(name) for name in ("networkx", "numpy", "scipy", "matplotlib")},
            "source_sha256": {relative: digest_file(root / relative) for relative in
                              ("src/task3_distributions.py", "src/task3_fitting.py", "src/task3_plotting.py", "src/run_task3.py")}}


def save_network(root: Path, identifier: str, graph: nx.Graph, samples: dict, observations: dict, model: dict | None,
                 config: dict, context: dict, logger: logging.Logger) -> dict:
    start = time.perf_counter()
    records, metadata = {}, {}
    directory = root / "results/distributions"
    for metric in METRICS:
        values = samples[metric]
        summary = statistics(values)
        freq = empirical_frequencies(values, metric)
        bins = clustering_bins(values, config["clustering_interior_bins"]) if metric == "clustering" else None
        fit = fit_distribution(values, metric, identifier.split("_")[1], model, config)
        curves = curve_rows(fit, freq, bins)
        prefix = f"{identifier}__{metric}"
        paths = {"samples": directory / f"{prefix}__samples.csv", "frequencies": directory / f"{prefix}__frequencies.csv",
                 "curves": directory / f"{prefix}__fitted_curves.csv"}
        sample_rows = [{"network_id": identifier, "metric": metric, "observation_id": obs, "value": value.item()}
                       for obs, value in zip(observations[metric], values)]
        write_csv(paths["samples"], ("network_id", "metric", "observation_id", "value"), sample_rows)
        write_csv(paths["frequencies"], ("value", "count", "probability"), freq)
        write_csv(paths["curves"], ("model", "value", "probability", "selected", "kind"), curves)
        if bins is not None:
            paths["bins"] = directory / f"{prefix}__plot_bins.csv"
            write_csv(paths["bins"], ("kind", "left", "right", "value", "count", "probability"), bins)
        base = {"statistics": summary, "fit": fit, "graph_nodes": len(graph), "graph_edges": graph.number_of_edges()}
        records[metric] = {**base, "frequencies": freq, "bins": bins, "curves": curves}
        metadata[metric] = {**base, "files": {key: path.relative_to(root).as_posix() for key, path in paths.items()},
                            "sha256": {key: digest_file(path) for key, path in paths.items()}}
        logger.info("%s %s n=%d mean=%.12g var=%.12g fit=%s; %s", identifier, metric, len(values), summary["mean"], summary["population_variance"], fit["method"], fit["reason"])
    elapsed = time.perf_counter() - start
    write_json(directory / f"{identifier}__metadata.json", {"complete": True, "identity": context,
               "network_id": identifier, "metrics": metadata, "distribution_and_fit_seconds": elapsed})
    return records


def publish_summaries(root: Path, records: dict, context: dict, *, complete: bool, timing: dict) -> None:
    stats_rows, fits_rows = [], []
    for identifier in IDS:
        if identifier not in records:
            continue
        for metric, entry in records[identifier].items():
            stats_rows.append({"network_id": identifier, "metric": metric, "scope": SCOPES[metric], **entry["statistics"]})
            fit = entry["fit"]
            fits_rows.append({"network_id": identifier, "metric": metric, **{key: value for key, value in fit.items() if key != "parameters"},
                              "parameters_json": json.dumps(fit["parameters"], sort_keys=True),
                              "candidates_json": json.dumps(fit["candidates"], sort_keys=True)})
    tables = root / "results/tables"
    write_csv(tables / "task3_distribution_statistics.csv", STAT_FIELDS, stats_rows)
    write_csv(tables / "task3_fit_parameters.csv", FIT_FIELDS, fits_rows)
    write_json(tables / "task3_distribution_statistics.json", {
        "complete": complete, "network_order": list(IDS), "metrics": list(METRICS), "identity": context,
        "statistics": {identifier: {metric: entry["statistics"] for metric, entry in entries.items()} for identifier, entries in records.items()},
        "fits": {identifier: {metric: entry["fit"] for metric, entry in entries.items()} for identifier, entries in records.items()},
        "timing_seconds": timing, "visual_review": "pending assistant inspection of all PNG/PDF exports",
        "notes": ["ddof=0", "one observation per component, not node-weighted", "no model regeneration or full BFS",
                  "KS screen 0.10 is a descriptive plotting rule, not a p-value", "AIC comparisons condition on fit scope; no iid network inference",
                  "BA xmin chosen on data; no bootstrap power-law hypothesis confirmation", "zero/one clustering atoms separate from interior beta"]})


def verify_saved(root: Path, graphs: dict, task2: dict, config: dict, context: dict, *, require_figures: bool) -> dict:
    """Read every saved sample/frequency/bin/curve and derive its summary again."""
    payload = json.loads((root / "results/tables/task3_distribution_statistics.json").read_text())
    if payload["identity"] != context or set(payload["statistics"]) != set(IDS):
        raise ValueError("Stale or incomplete Task 3 context")
    stat_rows = read_csv(root / "results/tables/task3_distribution_statistics.csv")
    fits_rows = read_csv(root / "results/tables/task3_fit_parameters.csv")
    if len(stat_rows) != 24 or len(fits_rows) != 24:
        raise ValueError("Expected 24 statistics/fit rows")
    for identifier in IDS:
        metadata = json.loads((root / f"results/distributions/{identifier}__metadata.json").read_text())
        if not metadata["complete"] or metadata["identity"] != context:
            raise ValueError("Incomplete/stale network distribution checkpoint")
        samples = {}
        for metric, entry in metadata["metrics"].items():
            for key, relative in entry["files"].items():
                if digest_file(root / relative) != entry["sha256"][key]:
                    raise ValueError(f"Saved artifact changed: {relative}")
            rows = read_csv(root / entry["files"]["samples"])
            if any(row["network_id"] != identifier or row["metric"] != metric for row in rows):
                raise ValueError("Sample network/metric identifier mismatch")
            dtype = float if metric == "clustering" else int
            values = np.array([dtype(row["value"]) for row in rows])
            samples[metric] = values
            calculated = statistics(values)
            if calculated != entry["statistics"] or calculated != payload["statistics"][identifier][metric]:
                raise ValueError("Saved sample moments disagree with JSON")
            row = next(row for row in stat_rows if row["network_id"] == identifier and row["metric"] == metric)
            if any(float(row[key]) != value for key, value in calculated.items()):
                raise ValueError("Statistics CSV/JSON mismatch")
            expected = empirical_frequencies(values, metric)
            observed = read_csv(root / entry["files"]["frequencies"])
            if len(expected) != len(observed) or any(float(a["value"]) != b["value"] or int(a["count"]) != b["count"] or float(a["probability"]) != b["probability"] for a, b in zip(observed, expected)):
                raise ValueError("Saved empirical frequency mismatch")
            bins = clustering_bins(values, config["clustering_interior_bins"]) if metric == "clustering" else None
            if bins is not None:
                observed_bins = read_csv(root / entry["files"]["bins"])
                if len(observed_bins) != len(bins) or any(a["kind"] != b["kind"] or any(float(a[key]) != b[key] for key in ("left", "right", "value", "count", "probability")) for a, b in zip(observed_bins, bins)):
                    raise ValueError("Binned clustering probabilities mismatch")
            predicted = curve_rows(entry["fit"], expected, bins)
            observed_curves = read_csv(root / entry["files"]["curves"])
            if len(predicted) != len(observed_curves) or any(a["model"] != b["model"] or not math.isclose(float(a["probability"]), b["probability"], abs_tol=1e-14, rel_tol=1e-12) for a, b in zip(observed_curves, predicted)):
                raise ValueError("Saved fit curve probability mismatch")
            fit_row = next(row for row in fits_rows if row["network_id"] == identifier and row["metric"] == metric)
            if fit_row["method"] != entry["fit"]["method"] or json.loads(fit_row["parameters_json"]) != entry["fit"]["parameters"]:
                raise ValueError("Fit metadata CSV/JSON mismatch")
        validate_samples(identifier, graphs[identifier], samples, task2["results"][identifier])
    if require_figures:
        figures = json.loads((root / "results/tables/task3_figure_manifest.json").read_text())
        if len(figures) != 8 or sum(len(figure["panels"]) for figure in figures) != 24:
            raise ValueError("Expected eight composite figures and 24 panels")
        for figure in figures:
            with Image.open(root / figure["png"]) as image:
                image.verify()
            pdf = (root / figure["pdf"]).read_bytes()
            if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:] or b"/Subtype /Image" in pdf:
                raise ValueError("Invalid PDF or unexpectedly rasterized scientific export")
            if not figure["all_text_inside_canvas"]:
                raise ValueError("Text clipping detected")
    return {"status": "PASS", "networks": 6, "distributions": 24, "composites": 8 if require_figures else 0,
            "shortest_paths_recomputed": False, "models_regenerated": False,
            "checks": ["frozen Task 2 identities", "eccentricity min/max/mean match Task 2", "CSV/JSON/sample moments agree",
                       "all frequency/bin counts normalized", "component count and total-node sum", "clustering range and Power BA zeros",
                       "fit probabilities recomputed from saved parameters", "8 vector PDFs/PNGs, 24 panels, no canvas text clipping"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    guard_environment()
    logger = configure_log()
    started = time.perf_counter()
    before = input_snapshot(ROOT)
    config = json.loads((ROOT / "task3_config.json").read_text())
    context = identity(ROOT, config, before)
    tests = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True)
    atomic_text(ROOT / "results/logs/task3_tests.txt", tests.stdout + tests.stderr)
    logger.info("Unit tests: %s", (tests.stdout + tests.stderr).strip())
    if tests.returncode:
        raise RuntimeError("Tests failed before Task 3 execution")
    try:
        with ExitStack() as guard:
            for name in ("gnp_random_graph", "barabasi_albert_graph", "single_source_shortest_path_length", "eccentricity", "diameter", "radius"):
                guard.enter_context(patch.object(nx, name, side_effect=RuntimeError(f"Forbidden during Task 3: {name}")))
            task2, graphs = load_frozen_task2(ROOT)
            logger.info("Frozen six-graph Task 2 inputs/caches verified; generation and shortest-path calls are forbidden")
            if args.verify_only:
                verification = verify_saved(ROOT, graphs, task2, config, context, require_figures=True)
                if input_snapshot(ROOT) != before:
                    raise ValueError("Protected inputs changed")
                logger.info("VERIFY ONLY PASS in %.6f s: %s", time.perf_counter() - started, verification)
                return 0
            write_json(ROOT / "results/tables/task3_input_manifest.json", {"identity": context, "started_utc": datetime.now(timezone.utc).isoformat()})
            records, timing = {}, {}
            for identifier in IDS:
                network_start = time.perf_counter()
                samples, observation_ids = collect_samples(ROOT, identifier, graphs[identifier])
                validate_samples(identifier, graphs[identifier], samples, task2["results"][identifier])
                records[identifier] = save_network(ROOT, identifier, graphs[identifier], samples, observation_ids,
                                                  task2["models"].get(identifier), config, context, logger)
                timing[identifier] = time.perf_counter() - network_start
                publish_summaries(ROOT, records, context, complete=False, timing=timing)
            verify_saved(ROOT, graphs, task2, config, context, require_figures=False)
            figures = []
            for family in ("grqc", "power"):
                for metric in METRICS:
                    figure = render_composite(family, metric, records, ROOT / "results/plots/task3", config)
                    for key in ("png", "pdf"):
                        figure[key] = Path(figure[key]).relative_to(ROOT).as_posix()
                    figures.append(figure)
                    logger.info("Exported %s: Real/ER/BA panels, vector PDF + PNG", figure["figure_id"])
            write_json(ROOT / "results/tables/task3_figure_manifest.json", figures)
            verification = verify_saved(ROOT, graphs, task2, config, context, require_figures=True)
            if input_snapshot(ROOT) != before:
                raise ValueError("Task 2/raw/report inputs changed during Task 3")
            timing["pipeline_before_visual_review"] = time.perf_counter() - started
            publish_summaries(ROOT, records, context, complete=True, timing=timing)
            verification.update(protected_inputs_unchanged=True, visual_review="pending render inspection")
            write_json(ROOT / "results/tables/task3_verification.json", verification)
            logger.info("Task 3 numerical/export PASS in %.6f s; render inspection still required", time.perf_counter() - started)
        return 0
    except Exception:
        logger.exception("Task 3 FAILED; do not accept unfinished results/figures")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
