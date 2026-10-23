# Project Instructions — CSCI 4250 Assignment 1

> Scope: this `AGENTS.md` governs the project folder and its subfolders. It guides AI coding/Work assistants; the course PDF and the user's direct instructions remain the authoritative sources. If the two conflict, stop and ask rather than silently redefining the assignment.

## 1. Mission and operating mode

- Project: **Frontiers of Network Science (CSCI 4250), Fall 2026 — Assignment 1: Network Analysis and Visualization**.
- Local project root: `H:\work_space\Frontiers_of_Network_Science\Assignment_1`.
- Deadline: **Friday, October 23, 2026, 11:59 PM**, as printed in the assignment PDF. Do not assume that a calendar reminder has been scheduled.
- Individual assignment. The student remains responsible for running, understanding, verifying, interpreting, and submitting their own work. AI may provide planning, code scaffolds, tests, debugging, and editorial assistance; never claim that the student has independently verified something unless they have.
- Default response language to the user: **Chinese**. Use **clear academic English** for report prose, captions, variable names, code comments, and reproducibility documentation unless instructed otherwise.
- Operate in small, verifiable steps. On a new session: read this file, the requirements PDF, `Assignment 1.docx`, and `PROJECT_STATUS.md` before proposing or changing work.
- Inspect first, propose a short plan, perform the requested step, validate, update `PROJECT_STATUS.md`, and tell the user what changed and what remains.
- Ask before any destructive action, nontrivial dependency installation, broad file reorganization, external upload, publication, Git push, or final submission. Never submit to Submitty without the user's explicit approval.

## 2. Authoritative source materials

At project root (exact spelling may differ slightly; inspect the actual filenames):
- `Assignment1_Fall2026_Network_Analysis_and_Visualization.pdf`: binding assignment instructions and rubric.
- `Assignment 1.docx`: the student's two selected/approved network descriptions.

Real networks:
1. **ca-GrQc** (SNAP coauthorship): 5,242 nodes, 14,496 edges; undirected and unweighted. Original source: https://snap.stanford.edu/data/ca-GrQc.html ; data: https://snap.stanford.edu/data/ca-GrQc.txt.gz
2. **Western States Power Grid** (Newman's network data collection): 4,941 nodes, 6,594 edges; undirected and unweighted. Source: https://public.websites.umich.edu/~mejn/netdata/ ; data: https://public.websites.umich.edu/~mejn/netdata/power.zip

The listed node/edge counts are source metadata, not substitutes for verifying loaded graph counts. Do not claim dataset history, date range, or collection methods beyond what sources support. Preserve source URLs and relevant scholarly citations in the report.

## 3. Deliverables and grading checkpoints

**Required: 50 points**; optional visualization **up to 10 bonus points**.

- **Task 1 (5 pts):** describe *both* original networks: source, what nodes/edges mean, provenance and collection/construction background where available, original node/edge counts, direction/weights, scientific relevance. Must exceed the short selection description.
- **Task 2 (15 pts):** for **all six networks** (two real plus one ER and one BA per real network): exact diameter, radius and average eccentricity measured on LCC if disconnected; number of components and LCC size measured on whole graph; average degree and **population** degree variance on whole graph. Report measured sample sizes and definitions. For directed graphs, apply the PDF's directed-network rules (current two networks are undirected).
- **Task 3 (15 pts):** four distributions per graph: degree, eccentricity/longest-shortest-path distance (LCC if disconnected), local clustering coefficient, component size (entire graph). Produce all **24 graph-by-metric panels**; for eccentricity, clustering and component size also report mean and population variance per graph. Axes/titles/legends must be descriptive; use log scales where justified and an **appropriate** fit or a transparent `N/A` justification for degenerate distributions. Do not invent a power-law fit for every distribution.
- **Task 4 (9 pts):** compare real vs ER vs BA separately for both real datasets, quoting numerical evidence. Discuss heterogeneity, clustering, connected components, distances, model fit and important limitations. Do not assert a result before obtaining actual outputs.
- **Task 5 (6 pts):** document data cleaning, original vs analyzed counts, graph-generation parameters, actual generated edge counts, seeds, tool/package versions, commands, code and reproducible workflow.
- **Optional (+10 pts):** create meaningful, uncluttered vector network illustrations for the **two real networks**; document layouts, filters and encodings, include legends, export SVG/PDF (Gephi acceptable).
- **Submitty:** report PDF + code/scripts/notebooks/supporting materials + reproduction instructions. Bundle supporting files as ZIP if helpful. User manually reviews and approves submission.

## 4. Folder and file policy

Target layout (create folders as needed; do not delete existing source documents):

```text
Assignment_1/
  AGENTS.md                  # stable agent rules
  PROJECT_STATUS.md          # mutable progress and decisions
  README.md                  # reproducibility/run guide
  requirements.txt
  .gitignore
  Assignment 1.docx          # original: DO NOT MODIFY
  Assignment1_Fall2026_Network_Analysis_and_Visualization.pdf  # original: DO NOT MODIFY
  data/
    raw/                     # immutable downloaded data
    processed/               # derived edge lists / metadata
  src/                       # import, preprocessing, model generation, statistics, plots
  tests/                     # tests and consistency checks
  results/
    tables/                  # CSV + JSON measurements
    plots/                   # distribution plots (SVG/PNG/PDF)
    gephi/                   # optional Gephi files and vector figures
  report/                     # report source and exported PDF
```

- Never overwrite, mutate, or re-save original uploaded PDF/DOCX or `data/raw/` files.
- Treat generated plots, tables and reports as reproducible outputs, not source-of-truth input. Prefer deterministic scripts to manual calculations.
- Keep stable filenames and descriptive paths. Do not move/delete previous work without the user's approval.
- Do not commit large raw data, temporary outputs, cache files, Python venv or personal account information to Git. Gitignore raw large datasets unless the user explicitly wants them tracked. Store download URLs and checksum values when possible.
- Keep `AGENTS.md` stable. Put current progress, failed attempts, decisions and next steps in `PROJECT_STATUS.md`; add a concise session log entry after meaningful changes.

## 5. Statistical and algorithmic conventions

- Network representation: simple, undirected, unweighted `networkx.Graph` unless original data requires otherwise. When reading an edge list, avoid implicitly discarding isolated nodes; if source format cannot encode isolates, document the limitation.
- Inspect and log: comment/header handling, parsing, self-loops, duplicate/reversed edges, isolates, malformed records, input vs analyzed `N` and `M`, and any graph transformations. Never silently remove vertices to make counts match expected values.
- **ER**: `G(n,p)` with `p = 2*M/(n*(n-1))`; report expected edge count and *realized* edge count. A fixed `seed` makes one sample reproducible, not exactly edge-matched.
- **BA**: standard `nx.barabasi_albert_graph(n,m,seed=...)`; `m` must be a positive integer. With the NetworkX default initial star graph, edge count is `m*(n-m)`. Choose the integer minimizing absolute edge-count error; document the residual mismatch.
  - ca-GrQc reference: `m=3` gives 15,717 edges (vs 14,496).
  - Power Grid reference: `m=1` gives 4,940 edges (vs 6,594); `m=2` gives 9,878, farther away. `m=1` produces a tree, so zero clustering is a *model/parameter consequence*, not a discovered characteristic of the real grid. Mention the unfair edge-density mismatch in discussion.
  - Do not change to an extended BA model or manipulate edges silently. Seek the student's approval and label alternatives as sensitivity analyses.
- Use separate documented random seeds per graph or a clearly stated seed policy.
- Connected components and their size distribution: calculate on the **entire** original/analyzed graph. Record number of components and full distribution of one observation **per component**; do not silently weight by node size.
- For a disconnected graph, calculate shortest-path-based metrics and the eccentricity distribution on its largest connected component (LCC). Use the largest **weakly** connected component for directed graphs if encountered.
- Degree statistics: compute on the whole analyzed graph. For undirected graphs, verify `sum(degrees) == 2*M`; `mean_degree == 2*M/N` within numerical tolerance.
- Define variance consistently using `numpy.var(..., ddof=0)` for all reported population variances and explain this convention in the report.
- Clustering distribution: compute local clustering on the **whole graph**, with degree-0 and degree-1 vertices assigned NetworkX's default coefficient 0; document the choice.
- Eccentricity: get the longest *shortest* path from each LCC node (not the longest simple path). `diameter = max(eccentricities)`, `radius = min(eccentricities)`, `mean_eccentricity = mean(eccentricities)`. Compute exact shortest paths with BFS for unweighted graphs; cache the eccentricities, avoiding recomputation in Tasks 2 and 3. Warn if a computation may be expensive rather than silently switching to approximations.
- Log distribution normalization (count vs fraction), binning, and fitting method. Never apply `log(0)`; omit/handle zero-frequency bins with explanation. For degenerate component-size/other distributions, label a fit `N/A` and explain rather than fabricate a line.
- Provide underlying CSV/JSON numbers for figures. Preserve no more significant digits than the precision justifies, while retaining full precision in machine-readable data.

## 6. Code quality, validation and reporting

- Preferred environment: Windows 11, VS Code, **Conda environment `fons-a1` running Python 3.12**. Primary libraries: `networkx`, `numpy`, `pandas`, `matplotlib`, `scipy`, `pytest`; Gephi only for optional visuals.
- Use **only** the `fons-a1` environment for Python commands, installation, testing, and result generation. Do not create a `.venv`, install packages into `base`, or silently use the system Python.
- When invoking Python from a tool-managed or newly created shell, prefer `conda run -n fons-a1 --no-capture-output python ...` rather than assuming `conda activate` persists across shell invocations.
- Before project work, run `& .\scripts\preflight.ps1` from the project root. It checks the existing environment and local execution without installing packages. If `conda` is absent from `PATH`, use the verified local executable `C:\ProgramData\anaconda3\Scripts\conda.exe` (or an explicitly supplied, verified `-CondaExe`); this does not require changing `PATH` or shell profiles.
- If `conda` is unavailable in the agent shell, inspect the existing Conda installation and request the user's approval to configure access. As a fallback, obtain the absolute interpreter path using `conda run -n fons-a1 python -c "import sys; print(sys.executable)"` in a Conda-enabled terminal. Do not guess a hardcoded Miniconda/Anaconda path.
- Before analysis, prove interpreter identity using `sys.executable`, `sys.version`, and dependency imports; record the actual versions for Task 5. Ask before modifying environment packages or versions.
- **Local-vs-cloud boundary:** `H:` and this Windows Conda environment are usable only from a properly authorized local desktop execution context. Do not claim a cloud-only Work/Codex session has run code against the local drive. If local execution is unavailable, report the limitation and ask for local execution or user-provided outputs.
- Prefer pure, testable functions with explicit parameters, type hints and docstrings. Put execution behind `if __name__ == "__main__":` and provide a CLI or clearly documented run commands.
- Before concluding an analysis step, test a hand-constructed small path graph (eccentricity, components, degrees) and verify invariants: node/edge counts; LCC bounds; graph-generation reproducibility; finite means/variances; number of plotted panels; non-empty exported files.
- Time or RAM constraints: measure the bottleneck first. Improve caching and graph algorithms before choosing faster backends; if using `igraph`/other packages or approximations, make results and methodological differences explicit and get approval for deviations from assignment requirements.
- Never invent results, runtime logs, source citations, fitted coefficients, Gephi screenshots, or measured graph sizes. Distinguish **expected**, **preliminary**, and **verified** results.
- Include legends, meaningful units (`hops`, node counts, coefficients), labeled axes and figure numbering in final report. Refer to table/figure IDs in the discussion.
- Always check the final report against all rubric criteria before marking complete. Include a per-task validation checklist in `PROJECT_STATUS.md`.

## 7. Agent handoff: what to do each session

1. Read `AGENTS.md`, `PROJECT_STATUS.md`, the assignment PDF and network selection DOCX. Verify working directory; don't presume the cloud environment can access `H:` drive.
2. Show the user the current stage and the smallest useful next action; keep scope limited to the user's request.
3. Inspect existing work and Git status before edits. Prefer a diff/backup for changes that are difficult to undo.
4. Make changes in the relevant source files. Run a quick test and inspect artifacts. Do not mark a metric or plot verified unless it actually ran and was checked.
5. Update `PROJECT_STATUS.md` (tasks, newly produced files, parameters, blockers, tests and next step). Do not rewrite history or falsify past progress.
6. Report to user in Chinese: files changed, tests run/outcomes, decisions/limitations, and next recommended action. Ask for approval before external sharing/submission or irreversible operations.

## 8. Progress gates

- Gate A: original inputs verified, two graphs load, original versus processed counts documented.
- Gate B: four random graphs generated, seeds/parameters/realized sizes saved.
- Gate C: Task 2 metrics complete and independently sanity-checked on six graphs.
- Gate D: Task 3 distributions, statistical table, and labeled plots complete (24 panels).
- Gate E: Task 1 prose, Task 4 evidence-based comparison, Task 5 reproducibility complete.
- Gate F (optional): 2 clear real-network vector visualizations with methods and legends.
- Gate G: report and supplement review, no missing requirements, user approves final files; user performs Submitty submission.

## Visualization Workflow

### Matplotlib
- Use the existing Conda environment `fons-a1`.
- Generate all required statistical distribution plots with Python.
- Use the non-interactive `Agg` backend for automated plotting.
- Export plots to `results/plots/` in PNG and PDF formats.
- Include axis labels, legends, appropriate scales, and justified best-fit curves.
- Do not fabricate experimental data or fit inappropriate statistical models.

### Gephi
- Use Gephi only for the optional real-world network visualizations.
- Generate GEXF files through NetworkX.
- Include node attributes such as degree, clustering coefficient, and community ID where applicable.
- Save generated graph files in `results/gephi/`.
- Prefer ForceAtlas2 or Yifan Hu layouts when appropriate.
- Export final visualizations in SVG or PDF.
- Preserve the original graph and document any visualization-only filtering.
- If desktop Computer Use is unavailable, prepare files and provide GUI instructions rather than claiming to have operated Gephi.
- Do not install desktop software or modify system configuration without user approval.

### Validation
- Verify plots are readable and labels are not clipped.
- Check that graph statistics come from the intended dataset.
- Record tool versions and visualization settings.
- Update PROJECT_STATUS.md after verified work.

## Report authoring rules (append to existing AGENTS.md)

- The authoritative editable report source is `report/main.tex` and `report/sections/*.tex`.
- Edit only the relevant report section for each assignment task.
- Do not generate a new Word document or rewrite the entire report unless the user requests it.
- Use verified statistics from saved results; never invent or round away meaningful discrepancies.
- Compile via `report/build_report.ps1` using a local LaTeX distribution (not Conda).
- Use PNG for quick review and PDF vector figures inside LaTeX; preserve SVG exports when available.
- The output `report/report.pdf` is a draft until the user approves submission.
- Cite dataset provenance and methodological sources; match the professor's Task 1–5 requirements.
- After meaningful report edits, verify the PDF and update `PROJECT_STATUS.md`.
