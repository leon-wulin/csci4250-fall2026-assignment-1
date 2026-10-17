"""Validate the actual interpreter and scientific packages for CSCI 4250.

Run: conda run -n fons-a1 --no-capture-output python scripts/check_environment.py
"""
from __future__ import annotations

import os
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from tempfile import TemporaryDirectory

PACKAGES = ("networkx", "numpy", "pandas", "matplotlib", "scipy", "pytest")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "AGENTS.md", "README.md", "PROJECT_STATUS.md", "environment.yml",
    "requirements.txt", "Assignment 1.docx",
    "Assignment1_Fall2026_Network_Analysis_and_Visualization.pdf",
)
OUTPUT_DIRS = (
    "data/processed", "results/tables", "results/plots", "results/gephi", "report",
)


def check_project() -> None:
    """Verify source readability and output access using temporary probes."""
    print("Project root:", PROJECT_ROOT)
    if Path.cwd().resolve() != PROJECT_ROOT:
        raise RuntimeError("Run from the project root or use scripts/preflight.ps1")
    for relative in REQUIRED_FILES:
        with (PROJECT_ROOT / relative).open("rb") as source:
            if not source.read(1):
                raise RuntimeError(f"Empty required file: {relative}")
    for relative in ("data/raw", "src", "scripts", "tests", *OUTPUT_DIRS):
        if not (PROJECT_ROOT / relative).is_dir():
            raise RuntimeError(f"Missing directory: {relative}")
    for relative in OUTPUT_DIRS:
        with TemporaryDirectory(prefix="preflight-", dir=PROJECT_ROOT / relative) as probe:
            path = Path(probe) / "probe.txt"
            path.write_text("preflight", encoding="utf-8")
            if path.read_text(encoding="utf-8") != "preflight":
                raise RuntimeError(f"Output read/write failed: {relative}")
    print("PASS: Required files/directories and output read/write access")


def check_scientific_stack() -> None:
    """Exercise a tiny fixture and headless exports without real data analysis."""
    import matplotlib
    import networkx as nx
    import numpy as np
    import pandas as pd
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import shortest_path

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    graph = nx.path_graph(4)
    graph.add_node(4)
    degrees = np.array([degree for _, degree in graph.degree()])
    eccentricities = nx.eccentricity(graph.subgraph(range(4)))
    checks = (
        sorted(map(len, nx.connected_components(graph))) == [1, 4],
        list(eccentricities.values()) == [3, 2, 2, 3],
        degrees.sum() == 2 * graph.number_of_edges(),
        np.isclose(degrees.mean(), 1.2),
        np.isclose(degrees.var(ddof=0), 0.56),
        nx.average_clustering(graph) == 0,
        shortest_path(csr_matrix([[0, 1], [1, 0]]), directed=False)[0, 1] == 1,
    )
    if not all(checks):
        raise RuntimeError("Synthetic graph/array/SciPy check failed")
    with TemporaryDirectory(prefix="preflight-", dir=PROJECT_ROOT / "results/plots") as probe:
        table = pd.DataFrame({"degree": degrees})
        csv_path = Path(probe) / "fixture.csv"
        table.to_csv(csv_path, index=False)
        if not pd.read_csv(csv_path).equals(table):
            raise RuntimeError("pandas CSV round trip failed")
        figure, axes = plt.subplots()
        try:
            axes.plot(range(5), degrees)
            axes.set(xlabel="Synthetic node", ylabel="Degree")
            for suffix in ("png", "svg", "pdf"):
                path = Path(probe) / f"fixture.{suffix}"
                figure.savefig(path)
                if path.stat().st_size == 0:
                    raise RuntimeError(f"Empty plot export: {suffix}")
        finally:
            plt.close(figure)
    print("PASS: Synthetic graph, NumPy/SciPy, pandas CSV, and PNG/SVG/PDF export")


def check_environment() -> int:
    """Check interpreter identity before importing the scientific stack."""
    print("Python version:", sys.version.split()[0])
    print("Interpreter:", sys.executable)
    print("Conda prefix:", os.environ.get("CONDA_PREFIX", "<not set>"))
    print("Conda env:", os.environ.get("CONDA_DEFAULT_ENV", "<not set>"))
    if sys.version_info[:2] != (3, 12):
        print("ERROR: Expected Python 3.12")
        return 1
    env_name = Path(sys.prefix).name.casefold()
    if env_name != "fons-a1":
        print("ERROR: Interpreter is not from named environment fons-a1")
        return 1
    prefix = Path(sys.prefix).resolve()
    if (
        Path(sys.executable).resolve().parent != prefix
        or not (prefix / "conda-meta/history").is_file()
        or Path(os.environ.get("CONDA_PREFIX", "")).resolve() != prefix
    ):
        print("ERROR: Interpreter, Conda prefix, or environment metadata do not agree")
        return 1
    failed = False
    for package in PACKAGES:
        try:
            print(f"{package}: {version(package)}")
            import_module(package)
        except (PackageNotFoundError, ImportError, OSError) as exc:
            print(f"ERROR: {package}: {exc}")
            failed = True
    if failed:
        return 1
    try:
        check_project()
        check_scientific_stack()
    except Exception as exc:
        print(f"ERROR: Startup check failed: {exc}")
        return 1
    print("PASS: Python and required packages are accessible in fons-a1")
    return 0


def main() -> int:
    """Keep Matplotlib's cache in a writable, automatically cleaned directory."""
    previous_config = os.environ.get("MPLCONFIGDIR")
    try:
        with TemporaryDirectory(
            prefix="preflight-mpl-", dir=PROJECT_ROOT / "results/plots"
        ) as config_dir:
            os.environ["MPLCONFIGDIR"] = config_dir
            return check_environment()
    except OSError as exc:
        print(f"ERROR: Cannot prepare temporary plotting cache: {exc}")
        return 1
    finally:
        if previous_config is None:
            os.environ.pop("MPLCONFIGDIR", None)
        else:
            os.environ["MPLCONFIGDIR"] = previous_config


if __name__ == "__main__":
    raise SystemExit(main())
