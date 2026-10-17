# Implementation readiness and method plan

Date: 2026-10-17. Project: `H:\work_space\Frontiers_of_Network_Science\Assignment_1`.
This is a preparation document, not the assignment report or an implemented six-network pipeline.

## Verified inputs and open preprocessing choice

The machine-readable input audit is `results/tables/dataset_preflight.json`. Original files, sidecar text, PDF and DOCX are protected by SHA-256 checks before and after inspection.

| Dataset | Local format | Loaded nodes | Loaded edges | Self-loops | Components | LCC nodes |
|---|---|---:|---:|---:|---:|---:|
| ca-GrQc | `data/raw/ca-GrQc.txt/CA-GrQc.txt`, edge list | 5242 | 14496 | 12 | 355 | 4158 |
| Power Grid | `data/raw/power/power.gml`, GML | 4941 | 6594 | 0 | 1 | 4941 |

Both load as undirected, unweighted `networkx.Graph` objects; the ca-GrQc object still contains loops and therefore is not yet a loop-free simple graph. No processed dataset was created.

ca-GrQc contains 28,980 distinct ordered records: 14,484 nonloop pairs each appear in both orientations, and 12 self-loop records appear once. Exact repeated ordered records: zero. Its header's directed wording does not describe the intended undirected analysis; explicit conversion to `Graph` merges only reverse records. The edge list cannot declare isolates; the observed node count matches the header, but this does not independently prove that upstream isolates never existed.

Power Grid declares `directed 0`, has 6,594 source/target records, and has no exact or undirected duplicate records. Reading with `label=None` preserves all explicitly declared numeric node IDs. Source/target orientation in undirected GML does not imply directed edges. The sidecar identifies Watts and Strogatz and provides the 1998 Nature citation; the GML's 2006 Creator timestamp is a file-generation timestamp, not evidence of collection date.

The student subsequently supplied `data/raw/ca-GrQc.txt.gz` and `data/raw/power.zip`. Gzip integrity and ZIP CRC checks passed, and all three extracted files match archive payloads byte for byte. Local checksums do not independently authenticate upstream downloads; download times remain undocumented. No replacement download was performed.

**Required first implementation decision:** explicitly document the ca-GrQc loop policy. Recommend a derived loop-free copy retaining every node: expected N=5242, M=14484 by subtraction. This copy has not been created or measured. Preserve raw N/M in Task 1 and report analyzed N/M and the 12-loop transformation in Task 5. Keeping loops would require an explicit methodological justification and consistent model comparison; do not silently use the 14,496 reference for a loop-free graph.

## Planned models and seeds (not generated)

Use ER `G(n,p)` with `p=2M/[n(n-1)]`, based on the final analyzed N/M. Expected M is not realized M. Use the standard NetworkX BA default initial star graph and integer m minimizing `abs(m*(n-m)-M)`; break equal-count ties by choosing the smaller m.

| Basis | ER p | BA m | BA formula M | BA M minus target |
|---|---:|---:|---:|---:|
| ca-GrQc as loaded, M=14496 | 0.001055278280507905 | 3 | 15717 | +1221 |
| ca-GrQc proposed loop-free, M=14484 | 0.0010544047057723853 | 3 | 15717 | +1233 |
| Power Grid, M=6594 | 0.0005403026973346214 | 1 | 4940 | -1654 |

Power Grid BA m=2 would yield 9878 edges, a larger error (+3284). m=1 necessarily gives a tree and zero clustering; explicitly discuss the density mismatch and this parameter consequence in Task 4. Do not add/remove model edges to force an exact match.

Planned independent seeds: ca-GrQc ER `2026101701`, ca-GrQc BA `2026101702`, Power ER `2026101703`, Power BA `2026101704`. Each generation manifest will record model name, seed, n, p/m, expected edges, realized N/M, source graph fingerprint and package versions. Realized counts remain TBD until generation.

## Statistical conventions and tests

- Degree, local clustering, connected-component counts and one-observation-per-component size distribution: whole analyzed graph. Degree-zero/one clustering is zero.
- Variances: population variance `numpy.var(..., ddof=0)` throughout. Store full-precision machine-readable values.
- Diameter, radius, average eccentricity and eccentricity distribution: LCC. Choose a tied LCC deterministically by smallest node ID and record the choice. The two selected datasets are undirected; do not silently generalize these routines to directed graphs.
- Exact unweighted BFS from each LCC node once. Store node-aligned eccentricities and derive diameter/radius/mean/variance and Task 3's distribution from the same array. Do not call separate all-source shortest-path computations for each statistic. Do not retain an unnecessary N-by-N distance matrix.
- `tests/test_analysis_conventions.py` exercises tiny path/isolate, triangle/isolate, star, cycle and singleton fixtures; degree-sum, population variance, whole-graph clustering/components, one BFS per LCC node, standard BA edge formulas/tree property, seeded reproducibility and rejection of audit outputs directed at raw source files. All 15 tests, including the three existing environment guards, passed. These are reference-method tests, not validation of future production code.
- Appropriate fits, objective/diagnostics, normalization, bins and log-scale handling must be recorded by distribution type. Degenerate distributions receive a reasoned N/A, not an invented power law. A connected graph's component-size distribution has one observation.

## Planned caching and output contract

| Path | Intended contents | Status |
|---|---|---|
| `data/raw/` | Immutable manually supplied source files | Present; audited |
| `data/processed/` | Derived graphs and original-versus-analyzed metadata | Empty; implementation pending |
| `results/cache/` | Node-aligned degree/clustering/eccentricity arrays, component sizes, cache manifest | Prepared; no assignment caches |
| `results/tables/` | CSV/JSON statistics, generation manifests, per-panel distribution data | Input audit present; analysis pending |
| `results/plots/` | `{graph_id}__{metric}.png` and `.pdf`, 24 graph-by-metric panels | Export tools verified; final figures absent |
| `results/logs/` | Run logs, commands, failures and runtime metadata | Prepared; no analysis run |
| `results/gephi/` | Attributed GEXF, manual Gephi projects and optional SVG/PDF exports | Prepared; Gephi manually operated |
| `report/` | Student-reviewed Task 1-5 source and final PDF | No final report created |

Cache keys must include raw SHA-256, analyzed graph fingerprint (all node IDs, including isolates, plus canonical edges), preprocessing policy/version, model parameters and seed, algorithm/schema version and relevant package versions. An input, policy, seed, parameter or algorithm change invalidates the key. Use numeric NPZ arrays with `allow_pickle=False` plus JSON metadata. Validate shapes, node ordering, finite values, graph/LCC counts and artifact checksums before reuse. Build temporary files and replace only complete validated caches. Cache completion is recorded only after a successful full pass; partial eccentricity arrays must not be accepted as complete.

Future workflow: validate local environment and source checksums; preprocess with documented policy; generate and save seeded models/manifests; compute exact metrics once and persist caches; derive tables/distributions/figures from caches; perform Task 4 comparison using those numbers; document Task 5; prepare optional Gephi files/manual instructions; audit all rubric items with the student. The production CLI, cache implementation, full figure count checks and end-to-end regeneration remain implementation work.

## Commands currently implemented

From the project root, use the existing environment only:

```powershell
& .\scripts\preflight.ps1
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python scripts/inspect_datasets.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python -m pytest tests -q
```

Git is initialized on `main`, with `origin` pointing to the public repository https://github.com/leon-wulin/csci4250-fall2026-assignment-1 . `.gitignore` exclusions for raw data, caches and logs were verified. The student approved the initial baseline commit and push on 2026-10-17. Git history and the remote branch record the resulting commit; full assignment analysis remains pending.
