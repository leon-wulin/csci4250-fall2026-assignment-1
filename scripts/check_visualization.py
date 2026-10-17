"""Export a synthetic diagnostic plot, not an assignment figure.

Run with fons-a1 from the project root; --output-dir must be a new directory
inside results/plots. The caller may inspect and then remove these temporary files.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    plots = (root / "results/plots").resolve()
    prefix = Path(sys.prefix).resolve()
    if (
        sys.version_info[:2] != (3, 12)
        or prefix.name.casefold() != "fons-a1"
        or Path(sys.executable).resolve().parent != prefix
        or Path(os.environ.get("CONDA_PREFIX", "")).resolve() != prefix
        or not (prefix / "conda-meta/history").is_file()
    ):
        parser.error("Run through conda run -n fons-a1 with Python 3.12")
    if Path.cwd().resolve() != root:
        parser.error("Run from the project root")
    if not output.is_relative_to(plots) or output == plots or output.exists():
        parser.error("Choose a new diagnostic subdirectory of results/plots")
    for directory in (plots, root / "results/gephi"):
        directory.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="visualization-cache-", dir=plots) as cache:
        previous_config = os.environ.get("MPLCONFIGDIR")
        os.environ["MPLCONFIGDIR"] = cache
        try:
            import matplotlib
            import networkx as nx
            import scipy
            from PIL import Image

            matplotlib.use("Agg")
            from matplotlib import pyplot as plt

            graph = nx.path_graph(4)
            output.mkdir()
            figure, axes = plt.subplots(figsize=(6.4, 4), layout="constrained")
            try:
                axes.plot(
                    list(graph.nodes), [degree for _, degree in graph.degree()],
                    marker="o", label="Four-node synthetic path",
                )
                axes.set(
                    title="Visualization tool check (synthetic)",
                    xlabel="Synthetic node index", ylabel="Degree (edges)",
                    xticks=range(4), ylim=(0.5, 2.5),
                )
                axes.legend(loc="lower center")
                axes.grid(alpha=0.25)
                for suffix in ("png", "pdf"):
                    figure.savefig(output / f"tool_check.{suffix}", dpi=150)
            finally:
                plt.close(figure)
            png = output / "tool_check.png"
            pdf = output / "tool_check.pdf"
            with Image.open(png) as image:
                image.verify()
            with Image.open(png) as image:
                image.load()
                dimensions = list(image.size)
                if dimensions != [960, 600]:
                    raise RuntimeError(f"Unexpected PNG dimensions: {dimensions}")
            pdf_bytes = pdf.read_bytes()
            if not pdf_bytes.startswith(b"%PDF-") or not pdf_bytes.rstrip().endswith(b"%%EOF"):
                raise RuntimeError("Invalid PDF header or end marker")
            metadata = {
                "purpose": "Temporary visualization tool check; synthetic data only",
                "python": sys.version.split()[0], "executable": sys.executable,
                "versions": {name: version(name) for name in ("matplotlib", "scipy", "networkx")},
                "backend": matplotlib.get_backend(), "png_dimensions": dimensions,
                "files": {
                    path.name: {"bytes": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}
                    for path in (png, pdf)
                },
            }
            (output / "tool_check.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(metadata, indent=2))
            print("PASS: PNG decoded and PDF structure markers verified; render PDF for visual review")
        finally:
            if previous_config is None:
                os.environ.pop("MPLCONFIGDIR", None)
            else:
                os.environ["MPLCONFIGDIR"] = previous_config
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
