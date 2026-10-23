"""Eight three-panel, vector-PDF scientific comparisons; never invoke LaTeX."""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib import ticker
import numpy as np

from src.task3_distributions import METRICS

LABELS = {
    "binomial_reference": "Binomial model reference",
    "hurdle_shifted_poisson": "Hurdle shifted Poisson MLE",
    "hurdle_shifted_nbinom": "Hurdle shifted NB MLE",
    "bounded_binomial": "Bounded binomial MLE",
    "bounded_beta_binomial": "Beta-binomial MLE",
    "bounded_discrete_normal": "Bounded discrete normal MLE",
    "discrete_power_law_tail": "Discrete power-law tail MLE",
    "discretized_lognormal_tail": "Discrete lognormal tail MLE",
    "zero_one_inflated_beta": "Beta-mixture bin probabilities",
    "reflected_kde_mixture": "Reflected KDE bin probabilities",
}
TITLES = {"degree": "Degree distribution", "eccentricity": "Eccentricity distribution",
          "clustering": "Local clustering coefficient distribution", "component_size": "Connected-component size distribution"}
XLABELS = {"degree": "Degree k (all nodes)", "eccentricity": "Eccentricity (hops; LCC nodes)",
           "clustering": "Local clustering coefficient C (all nodes)", "component_size": "Component size (nodes per component)"}


def fit_note(fit: dict) -> str:
    if fit["status"] == "N/A":
        return "Fit N/A: " + fit["reason"]
    note = LABELS[fit["method"]] + f"; KS={fit['ks']:.3f}."
    if "xmin_search" in fit:
        power = next(c for c in fit["candidates"] if c["method"] == "discrete_power_law_tail")
        note += f" xmin={power['parameters']['xmin']}, tail n={power['n_fit']}, power-law alpha={power['parameters']['alpha']:.2f}."
    if "non-LCC" in fit["fit_scope"]:
        note += " Non-LCC fit only; LCC is not fitted."
    if "endpoint_masses" in fit:
        note += " Endpoints are separate point masses."
    return note


def assert_text_inside(figure) -> None:
    """Fail on text clipping beyond a small antialiasing tolerance."""
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    bounds = figure.bbox
    boxes = [ax.get_tightbbox(renderer) for ax in figure.axes]
    boxes += [text.get_window_extent(renderer) for text in figure.texts if text.get_visible() and text.get_text()]
    for ax in figure.axes:
        legend = ax.get_legend()
        if legend is not None and legend.get_window_extent(renderer).overlaps(ax.bbox):
            raise ValueError("Legend overlaps the data area")
    for box in boxes:
        if box.width == 0 or box.height == 0:
            continue
        if box.x0 < bounds.x0 - 2 or box.y0 < bounds.y0 - 2 or box.x1 > bounds.x1 + 2 or box.y1 > bounds.y1 + 2:
            raise ValueError("Figure axes/labels/annotations exceed the canvas")


def render_composite(family: str, metric: str, records: dict, output: Path, config: dict) -> dict:
    """All empirical positive-frequency values are shown, including value zero."""
    identifiers = [family + "_" + model for model in ("real", "er", "ba")]
    entries = [records[i][metric] for i in identifiers]
    all_probabilities = [row["probability"] for entry in entries
                         for row in (entry["bins"] if metric == "clustering" else entry["frequencies"]) if row["count"] > 0]
    use_log_y = max(all_probabilities) / min(all_probabilities) >= 30
    min_probability = min(all_probabilities) * 0.5
    max_x = max(entry["statistics"]["maximum"] for entry in entries)
    min_x = min(entry["statistics"]["minimum"] for entry in entries)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 10.5, "axes.labelsize": 10,
                         "legend.fontsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=config["figure_size_inches"], sharey=True)
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.32, top=0.70, wspace=0.13)
    drawn_observations = []
    for panel, (identifier, entry, ax) in enumerate(zip(identifiers, entries, axes)):
        summary = entry["statistics"]
        empirical = entry["bins"] if metric == "clustering" else entry["frequencies"]
        nonempty = [row for row in empirical if row["count"] > 0]
        if sum(row["count"] for row in nonempty) != summary["n_samples"]:
            raise ValueError("Plot omitted observations")
        drawn_observations.append(summary["n_samples"])
        if metric == "clustering":
            interior = [row for row in nonempty if row["kind"] == "interior_bin"]
            endpoints = [row for row in nonempty if row["kind"] != "interior_bin"]
            if interior:
                ax.bar([row["value"] for row in interior], [row["probability"] for row in interior],
                       width=0.9 / config["clustering_interior_bins"], color="#2077a4", alpha=0.75, label="Interior bin probability")
            if endpoints:
                ax.scatter([row["value"] for row in endpoints], [row["probability"] for row in endpoints],
                           color="#174e76", marker="D", s=28, label="Exact 0/1 point masses", zorder=5)
            ax.set_xlim(-0.035, 1.035)
            ax.xaxis.set_major_locator(ticker.MultipleLocator(0.25))
        else:
            ax.scatter([row["value"] for row in nonempty], [row["probability"] for row in nonempty],
                       s=22, color="#2077a4", alpha=0.9, label="Empirical probability", zorder=3)
            if metric == "degree":
                ax.set_xscale("symlog", linthresh=1, linscale=0.6)
                ax.set_xlim(-0.15, max(2, max_x * 1.15))
                ticks = [v for v in (0, 1, 10, 100, 1000) if v <= max(2, max_x * 1.15)]
                ax.xaxis.set_major_locator(ticker.FixedLocator(ticks))
                ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
            elif metric == "component_size":
                ax.set_xscale("log")
                ax.set_xlim(0.8, max_x * 1.3)
                ax.scatter([summary["maximum"]], [1 / summary["n_samples"]], facecolors="none", edgecolors="#243a4e", s=85,
                           label="Selected LCC observation", zorder=4)
            else:
                ax.set_xlim(min_x - 0.65, max_x + 0.65)
                ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=6))
        curves = entry["curves"]
        for method in dict.fromkeys(row["model"] for row in curves):
            curve = [row for row in curves if row["model"] == method and row["probability"] > 0]
            if metric == "clustering":
                curve = [row for row in curve if row["kind"] == "interior_bin"]
            selected = method == entry["fit"]["method"]
            if curve:
                ax.plot([row["value"] for row in curve], [row["probability"] for row in curve],
                        color="#c24e24" if selected else "#777777", linestyle="--" if selected else ":",
                        linewidth=1.6, label=LABELS[method] if selected else "Power-law tail alternative")
        if use_log_y:
            ax.set_yscale("log")
            ax.set_ylim(min_probability, 1.8)
        else:
            ax.set_ylim(0, min(1.1, max(all_probabilities) * 1.3))
        title = ("Real", "ER", "BA")[panel]
        node_count, edge_count = entry["graph_nodes"], entry["graph_edges"]
        ax.set_title(f"({chr(97+panel)}) {title} | {identifier}\nN={node_count:,}, M={edge_count:,}; observations={summary['n_samples']:,}", y=1.36, pad=0)
        ax.set_xlabel(XLABELS[metric], labelpad=7)
        ax.grid(axis="y", color="#d0d5d8", linewidth=0.5, alpha=0.7)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), frameon=False)
        note = textwrap.fill(fit_note(entry["fit"]), width=57)
        ax.text(0, -0.30, note, transform=ax.transAxes, va="top", ha="left", fontsize=8.2, color="#434343")
    axes[0].set_ylabel("Probability per bin / endpoint mass" if metric == "clustering" else "Empirical probability")
    family_title = "ca-GrQc" if family == "grqc" else "Western States Power Grid"
    fig.suptitle(f"{family_title} | {TITLES[metric]}", fontsize=14, weight="bold", y=0.96)
    caption = ("Clustering: 20 equal-width interior bins; exact C=0 and C=1 masses are separate. Curves integrate fitted probability over each bin."
               if metric == "clustering" else "Discrete PMF = count / observations; component observations are unweighted components, not nodes.")
    caption += " Zero-valued observations are retained; empty-frequency bins are saved but not drawn on logarithmic y axes. Fits/smoothers are descriptive, not significance tests."
    fig.text(0.065, 0.035, textwrap.fill(caption, 153), va="bottom", fontsize=8.1, color="#444444")
    assert_text_inside(fig)
    output.mkdir(parents=True, exist_ok=True)
    stem = family + "__" + metric
    for suffix in ("png", "pdf"):
        fig.savefig(output / f"{stem}.{suffix}", dpi=config["png_dpi"], facecolor="white")
    plt.close(fig)
    return {"figure_id": stem, "panels": identifiers, "metric": metric, "empirical_observations_plotted": drawn_observations,
            "x_scale": "symlog (zero preserved)" if metric == "degree" else "log" if metric == "component_size" else "linear",
            "y_scale": "log" if use_log_y else "linear", "all_text_inside_canvas": True,
            "zero_count_bins_saved_not_plotted_on_log_y": True, "png": str(output / f"{stem}.png"), "pdf": str(output / f"{stem}.pdf")}
