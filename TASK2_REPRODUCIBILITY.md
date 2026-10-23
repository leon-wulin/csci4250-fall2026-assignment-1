# Task 2 computation and reproduction

Verified on 2026-10-18, using the existing Windows project root
`H:\work_space\Frontiers_of_Network_Science\Assignment_1` (underscore, not space).
This document covers computation only, not report writing or Task 3.

## Environment and commands

Only use `fons-a1`: Python 3.12.15, NetworkX 3.7, NumPy 2.5.4,
pandas 2.3.3, SciPy 1.18.1, pytest 9.1.1. No dependency was installed or changed.

From the project root:

```powershell
& .\scripts\preflight.ps1
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python -m pytest tests -q -p no:cacheprovider
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python src/run_task2.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python src/run_task2.py --verify-only
```

If `conda` is on PATH, the equivalent entrypoint is exactly:
`conda run -n fons-a1 --no-capture-output python src/run_task2.py`.
The script independently guards interpreter identity and runs all tests before
generating assignment models or computing distances. `--verify-only` regenerates
the four seeded models for topology comparison but does not run full BFS or
replace numerical result tables. Logs use UTC explicitly.

## Inputs and approved preprocessing

The unchanged original baseline is `results/tables/dataset_preflight.json`.
The pipeline reuses its auditor in `scripts/inspect_datasets.py`, saves a fresh
audit as `results/tables/task2_input_audit.json`, and checks baseline hashes.
Unexpected raw sizes, changed source hashes, malformed records, directedness,
weights or additional preprocessing changes cause a failure before analysis.

- ca-GrQc raw: 5242 nodes, 14496 undirected edges including 12 self-loops.
  The 28980 ordered records consist of 14484 reciprocal nonloop pairs and
  12 loop records; exact repeated ordered records are absent. Reciprocal
  records are interpreted as one undirected edge, not as additional weights.
- The student explicitly approved deleting only the 12 loops in a derived
  copy. Analyzed size: 5242 nodes, 14484 edges, 355 components, LCC 4158.
  Node 12295 becomes isolated after removal of its only self-loop; it is
  retained, so the analyzed graph has one isolate and no removed vertices.
- Power Grid: GML read with `label=None`; 4941 nodes, 6594 edges, no loops or
  duplicate edge records, one component, no isolates. Numeric IDs are retained.
- Derived GraphML files contain unweighted topology with integer node IDs.
  Non-topological source attributes are not required for these computations.
  Raw inputs, the selection DOCX, assignment PDF, AGENTS.md and official LaTeX
  source/output are hashed before and after the run and remain unchanged.
- The edge-list format cannot declare upstream isolates. No missing vertices
  are synthesized. Local checksums establish file identity, not independent
  authentication against an upstream checksum; download times remain unknown.

## Models and seeds

`task2_config.json` records the approved policy. All four models use **seed=42**,
superseding the four historical seeds in the readiness documents. One seeded
sample is generated per model; samples are not selected/retried to match M.
Model IDs 0..N-1 are synthetic identifiers, not author or facility identities.

ER uses `nx.gnp_random_graph(n, p, seed=42)`, where `p=2*M/(N*(N-1))`
is computed from the analyzed real network without pre-rounding.
BA uses `nx.barabasi_albert_graph(n, m, seed=42)` with its default initial star.
Choose the valid integer m minimizing `abs(m*(n-m)-target_M)`; choose smaller m
if tied. Standard BA has exactly `m*(n-m)` edges with this initialization.

| Network | p or m | Target M | Actual M | Signed difference | Absolute relative difference |
|---|---|---:|---:|---:|---:|
| grqc_er | p=0.0010544047057723853 | 14484 | 14176 | -308 | 2.126484% |
| grqc_ba | m=3 | 14484 | 15717 | +1233 | 8.512842% |
| power_er | p=0.0005403026973346214 | 6594 | 6431 | -163 | 2.471944% |
| power_ba | m=1 | 6594 | 4940 | -1654 | 25.083409% |

Power BA m=2 would yield 9878 edges, farther from the target than m=1.
The density mismatch and m=1 tree property are model limitations, not measured
characteristics of the real Power Grid. No edges are added/deleted to force a match.
Relative difference is `abs(actual_M-target_M)/target_M`, stored as a fraction;
the signed relative difference is also saved separately.

## Exact statistics and retained arrays

For each of `grqc_real`, `grqc_er`, `grqc_ba`, `power_real`, `power_er`, `power_ba`:

- Whole analyzed graph: N, M, components, LCC node count, mean degree and degree
  population variance (`ddof=0`). Degree-zero nodes contribute to both statistics.
- Largest connected component: exact unweighted BFS once per node. Each node's
  eccentricity is the maximum shortest-path distance, not longest simple path.
  Diameter/max, radius/min and average eccentricity reuse that single array.
  Average eccentricity is not average shortest-path length. Distances are hops.
- Equal-size LCC ties use the smallest numeric node ID. A singleton's eccentricity
  is zero. Empty/directed/multigraph/weighted inputs are explicitly rejected.
- No full all-pairs distance matrix, approximations, clustering calculation,
  distribution fitting or plotting is performed.

Validation includes exact small-graph references; one-BFS-per-node counting;
degree sum 2M; mean degree 2M/N; component partition/LCC bounds; radius <= mean
eccentricity <= diameter <= 2*radius; adjacent eccentricity difference <=1;
finite statistics; seeded model reproducibility; BA edge formula; GraphML
round-trip; and machine-readable output/cache consistency.

## Output contract

Paths below are relative to the confirmed project root. Every output is local;
nothing was committed, pushed or uploaded.

| Pattern/path | Contents |
|---|---|
| `results/tables/task2_global_properties.csv` | Six rows with all nine requested metrics, IDs, isolates, degree sum, timings and graph fingerprint |
| `results/tables/task2_global_properties.json` | Full-precision results, complete flag, models, preprocessing, environment/code/source identities and verification |
| `results/tables/task2_model_parameters.csv` | Four models, exact p/m, seed, target/expected/actual counts and signed/absolute/relative deviations |
| `results/tables/task2_input_audit.json` | Fresh read-only raw/archive audit; includes duplicate/reciprocal records and self-loops |
| `results/tables/task2_preprocessing.json` | Original-versus-analyzed counts and explicit loop removal/node retention |
| `results/tables/task2_verification.json` | Final six-network verification PASS |
| `results/tables/task2_artifact_manifest.json` | Handoff inventory of all output/source/documentation files, sizes and SHA-256 values (excludes its own recursive hash); regenerate after future runs |
| `data/processed/task2/<network_id>.graphml` | All six reusable graphs, including all isolated vertices |
| `results/cache/eccentricity_<network_id>.csv` | LCC node ID and exact eccentricity, with network ID |
| `results/cache/degrees_<network_id>.csv` | Every full-graph node ID and degree |
| `results/cache/components_<network_id>.csv` | One row per component: deterministic index, size, smallest node ID |
| `results/cache/task2_<network_id>.json` | Per-network completion manifest, identity, result and artifact checksums |
| `results/logs/task2_execution.log` | Append-only UTC progress, warnings, timings, validation and cache-reuse messages |
| `results/logs/task2_tests.txt` | Latest pre-analysis test output |

Read GraphML with `nx.read_graphml(path, node_type=int)` to restore integer IDs.
Caches/logs remain ignored by Git but are present locally and reproducible.
All machine-readable floating-point values retain round-trip precision; rounding
in this document or a future report is only for presentation.

## Cache identity, interruption and timing

Each cache identity includes canonical graph topology and all node IDs, source
hashes, approved configuration/seed, Python/package versions, algorithm version
and actual computation/entrypoint/auditor code hashes. A changed identity is
logged and recomputed. Corrupted matching artifacts fail validation rather than
being silently reused. A completion manifest is published last, after atomic
CSV writes. Partial networks cannot masquerade as complete caches.

After every successful network, its cache and the global partial tables are
saved. `complete=true` is published only after all six networks, with a final
cross-check; a failed final check resets it to false. Restarting the normal
command reuses completed matching caches and reruns only incomplete/invalidated
analyses. An interrupted current network may need its own BFS pass again.

The first complete pipeline took **56.306285 seconds** excluding the outer Conda
launcher. Per-network `analysis_seconds` includes exact BFS plus metric validation,
but excludes graph generation and artifact I/O; `eccentricity_seconds` is its BFS
subset. Model generation has a separate `generation_seconds` field. Cache hits
retain original computation times, not misleading near-zero replacement times.
An independent `--verify-only` pass took 6.463838 seconds. A separate actual-data
probe verified all six cache hits with BFS calls explicitly forbidden.

All **38 tests passed** before the complete run and again in fresh-process
verification. The report and Task 1 remain unchanged. Await student review
before report integration or Task 3.
