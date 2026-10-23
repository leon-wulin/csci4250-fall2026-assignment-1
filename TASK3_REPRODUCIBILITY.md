# Task 3: distributions, fitting and export

## Verified scope and commands

Run from `H:\work_space\Frontiers_of_Network_Science\Assignment_1` using the existing `fons-a1` environment:

```powershell
& .\scripts\preflight.ps1
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python src/run_task3.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python src/run_task3.py --verify-only
```

The normal command rewrites only reproducible Task 3 outputs. It first runs all tests and verifies the frozen six Task 2 GraphML files, configuration, model metadata, graph fingerprints and saved degree/component/eccentricity caches. It neither regenerates assignment models nor computes shortest paths. NetworkX generation/distance entry points are guarded against accidental use during production execution. Tests may use small synthetic graphs. Never invoke Task 2 just to reproduce Task 3: Task 2 verification can regenerate model graphs.

Graph order is `grqc_real`, `grqc_er`, `grqc_ba`, `power_real`, `power_er`, `power_ba`. All four existing model seeds remain 42. The approved derived ca-GrQc graph has 5242 nodes and 14484 edges after removing 12 self-loops, including the retained isolated vertex; raw data are unchanged. Power BA remains the standard m=1 tree with 4940 edges, not an edge-matched grid model.

## Handoff after regenerating Task 2 or editing the report

Task 2's handoff inventory is a saved snapshot, not an automatically refreshed
index. After a successful new Task 2 production run, and before running Task 3,
use the existing fons-a1 environment to run:

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python scripts/refresh_task2_manifest.py --write
```

Without `--write`, this utility performs a read-only validation. It checks the
six frozen graphs, source/configuration identities, caches and numerical tables
through `load_frozen_task2` before publishing any refreshed output checksums.
The write mode preserves the previous manifest and its historical documentation
evidence; it does not regenerate graphs, shortest paths or measurements.

Report edits also change Task 3's protected-input identity. Run the normal Task 3
command to generate outputs with the current report snapshot, then verify them
before rebuilding the report PDF. An older verify-only snapshot is intentionally
rejected after protected inputs change. No full production rerun was performed
during Task 5 authoring; the new utility's read-only mode was checked against the
existing six-network artifacts. For pytest temporary-directory access errors,
set process-local TEMP and TMP to a new writable project-local directory, as
shown in the report's reproduction commands.

## Observations and normalization

- Degree and local clustering: one observation per node in the full graph, including isolates and degree-1 vertices. NetworkX assigns clustering 0 to degree-0/1 vertices.
- Eccentricity: one exact cached observation per LCC vertex. No approximate or new shortest-path calculation is used.
- Component size: one observation per connected component over the entire graph, not node-weighted. The LCC remains in all samples, frequencies and moments.
- Every variance is the population variance (`ddof=0`). Samples and unrounded moments are saved separately from presentation figures.
- Discrete frequencies use count / total observations. Dense integer frequency tables retain empty bins. Clustering saves exact unique-value frequencies and a separate 20-bin equal-width interior histogram: C=0 and C=1 are separate exact point masses, not mixed into the interior bins. Each interior bin probability is divided by all graph nodes.
- Degree x axes use symlog with a linear region around zero; component-size x axes use log. Y axes use log when the positive empirical mass range justifies it. Zero-valued observations are always retained and plotted; only zero-frequency bins cannot appear on a logarithmic y axis. Shared axis ranges within each family support comparison.

## Fitting policy and limitations

All fitting is descriptive. Nodes/components within a network need not be independent. A KS distance threshold of 0.10 is a predeclared plotting screen, **not a p-value or significance test**. AIC is compared only within the same fitted sample/scope; no bootstrap goodness-of-fit or power-law hypothesis test was performed. Configurations and all candidate diagnostics, including rejected/boundary-limited candidates, are saved in `task3_config.json` and the fit CSV/JSON.

1. **ER degree:** the exact Binomial(N-1,p) marginal reference uses the original full-precision Task 2 probability, not the realized mean degree. No degree parameter is re-estimated.
2. **Real degree:** a hurdle mass at zero plus shifted Poisson or shifted negative binomial for positive degrees. MLE/AIC with the descriptive KS screen selected negative binomial for both real networks.
3. **BA degree:** exact discrete power-law MLE with Hurwitz-zeta normalization. Select xmin by minimum discrete KS, requiring at least max(100, ceil(0.02N)) tail samples and five distinct tail values; compare a discretized lognormal on the same tail. Selected ca-GrQc: xmin=6, tail n=1527, alpha=2.8283146192474082. Selected Power: xmin=5, tail n=326, alpha=2.782552889621333. Curves are multiplied by the empirical tail fraction; the body remains empirical and is not fitted. AIC differences from lognormal are only about 1.71 and 1.69, respectively; this is weak model discrimination. The ca-GrQc lognormal alternative hits its optimization boundary (mu=-20), so it is not a reliable competing optimum. Neither fit establishes a universal power law or an exponent confidence interval.
4. **Eccentricity:** compare bounded binomial, beta-binomial and a discretized truncated normal on the observed integer support [radius, diameter]. Five networks select the bounded discrete normal; Power BA selects beta-binomial. Data-selected bounds make these descriptive within-sample fits, not predictions beyond the observed support.
5. **Clustering:** exact empirical endpoint masses plus conditional interior Beta MLE. The four sufficiently populated interior datasets fail the Beta KS screen, so their figures use a boundary-reflected Gaussian KDE (Scott bandwidth) as an explicitly labeled descriptive smoother. KDE curves integrate probability over the displayed bins, with endpoint mass excluded. KDE is not parametric acceptance and receives no AIC claim. Power ER has only eight interior samples and Power BA has none: both are N/A, with all observations still shown. Power BA's all-zero clustering is a consequence of the standard m=1 tree, not an empirical discovery about the real grid.
6. **Components:** retain the LCC as an explicit empirical point and fit only non-LCC sizes when at least 50 observations and three distinct values are available. Only Power ER supports a screened shifted-negative-binomial description. ca-GrQc real's candidates fail the screen; ca-GrQc ER has only 18 non-LCC observations; the three connected graphs have one observation and zero variance. These five component panels are N/A, not fitted artificial curves. All component summary statistics still include the LCC.

Methodological background: Clauset, Shalizi and Newman (2009), *Power-law distributions in empirical data*, https://arxiv.org/abs/0706.1062 . The present code intentionally stops short of that paper's full hypothesis-testing/bootstrap workflow. SciPy distribution definitions: https://docs.scipy.org/doc/scipy/reference/stats.html .

## Files and reuse

- `src/task3_distributions.py`: frozen-input verification, samples, frequencies, bins, moments and invariants.
- `src/task3_fitting.py`: candidate MLEs, scoped model selection, reflected KDE, diagnostics and curve probabilities.
- `src/task3_plotting.py`: Agg backend, three-panel composites, layout/legend assertions and PNG/vector PDF exports.
- `src/run_task3.py`: orchestration, per-network checkpoints, logs, provenance and independent saved-artifact verification.
- `tests/test_task3.py`: zero preservation, scope/cache reuse, degeneracy, normalization, integer support, ER reference, KDE, tail fitting, KS jumps and composite export checks.
- `results/tables/task3_distribution_statistics.{csv,json}`: 24 graph-by-metric summary rows/full-precision JSON, configuration/source identities, fits and timings.
- `results/tables/task3_fit_parameters.csv`: 24 fit/reference/smoother/N/A records with complete candidate parameters and reasons.
- `results/distributions/`: 24 sample CSVs, 24 frequency CSVs, 24 fitted-curve CSVs (header-only for N/A), six clustering bin CSVs, six per-network metadata/checksum JSONs: 84 files in total.
- `results/plots/task3/`: eight composites named `{grqc,power}__{degree,eccentricity,clustering,component_size}`, each PNG plus vector PDF (16 exports, 24 panels). PNGs are 3000 x 1160 pixels; PDFs are one page, 1080 x 417.6 pt.
- `results/tables/task3_{input_manifest,figure_manifest,verification,visual_review,artifact_manifest}.json`: input fingerprints, panel inventory, verification, inspected-export hashes and handoff inventory.
- `results/logs/task3_execution.log`, `task3_tests.txt`: append-only execution history and latest test output. `results/logs/task3_review/` contains ignored PDF review renders and diagnostics.

Task 3 outputs have configuration, graph, code, environment and protected-input identities; verification rejects a mismatch rather than silently accepting stale data. Successful per-network data are checkpointed, but the normal command intentionally recomputes the cheap distributions/fits instead of resuming a partly completed fit/export run. Expensive Task 2 eccentricities are always reused. Re-running plotting invalidates the prior visual review: inspect all regenerated exports again.

## Verification on 2026-10-22

- Environment: Python 3.12.15, NetworkX 3.7, NumPy 2.5.4, pandas 2.3.3, Matplotlib 3.11.2, SciPy 1.18.1, pytest 9.1.1; no dependency changes.
- Final production run: 55 tests passed in 2.06 s; numerical/export pipeline logged 21.231045 s (JSON checkpoint at 21.1571975 s). Per-network sample/fitting times: grqc_real 0.353906 s; grqc_er 0.320046 s; grqc_ba 0.368049 s; power_real 0.288304 s; power_er 0.298089 s; power_ba 0.317864 s. These exclude global startup/input verification and figure exports and are not shortest-path benchmarks.
- Fresh-process verify-only: 55 tests passed in 2.09 s; all saved results verified in 12.258922 s, including startup/tests/input loading. Verified CSV/JSON/sample moments, all frequency/bin totals, Task 2 eccentricity min/max/mean, component observations/sums, coefficient ranges, Power BA zeros, fitted-curve probabilities, six graph identities, 8 composites/24 panels and 38 unchanged Task 2 computational artifact hashes.
- All eight final PNGs and all eight final PDFs rendered with Poppler were inspected by the assistant. Titles, axes, legends, endpoint/giant-component observations and annotations are readable and unclipped. Legends were moved outside plotting areas after an initial review. This is assistant verification, not a claim of independent student review.
- Final classification: 11 descriptive parametric fits, two exact ER references, four descriptive KDE smoothers and seven documented N/A cases. No critical computational or export failure remains. Review the descriptive fitting choices before report integration.
- Original raw files, course PDF/DOCX, AGENTS.md, all Task 2 computational files and the entire official LaTeX report remain unchanged. No Task 4, Gephi operation, dependency installation, commit, push or submission occurred.

Stop at this handoff. Report integration and Task 4 require the student's next instruction.
