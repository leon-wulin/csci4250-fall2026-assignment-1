# Windows 11 project handoff

## Obtain this snapshot

Clone the existing repository on the destination computer:

```powershell
git clone https://github.com/leon-wulin/csci4250-fall2026-assignment-1.git
cd csci4250-fall2026-assignment-1
git log -1 --oneline
```

For an existing clean clone, use `git pull --ff-only`. If local edits exist,
review and preserve them before updating. Do not reset or overwrite them.
The destination directory need not be on H:. Paths mentioning H: in historical
records describe the original host, not a required drive mapping.
The repository's `.gitattributes` preserves file bytes across checkouts because
the analysis manifests use SHA-256 checksums.

## Files included and excluded

The snapshot includes the original assignment PDF/DOCX, project instructions,
source, tests, configurations, six saved GraphML graphs, numerical tables,
Task 3 distribution samples and plots, and the current LaTeX/PDF report draft.
The report remains a draft awaiting student review. Gephi layouts and final
optional vector visualizations have not been verified.

The existing ignore policy excludes `data/raw/`, `results/cache/`,
`results/logs/`, `report/build/`, Python environments and editor settings.
Therefore cloning alone does **not** restore the complete execution state.

For Gephi visualization, the saved real networks are available directly:

- `data/processed/task2/grqc_real.graphml`: 5,242 nodes, 14,484 edges.
- `data/processed/task2/power_real.graphml`: 4,941 nodes, 6,594 edges.

These graphs do not establish that the proposed visualization attributes or
layouts are already prepared. Check or add the desired node attributes before
styling. Preserve the analyzed topology and document visualization-only filters.

To reuse exact computations without rerunning BFS, separately copy the original
`data/raw/` and `results/cache/` directories through a user-approved transfer
method. Preserve their relative paths. Saved manifests provide integrity checks.
Without those directories, full pipeline verification is expected to fail;
do not treat that as evidence that the saved graphs or figures are invalid.
Raw input download URLs and audit details are documented in the project.

### Known verification issue in this snapshot

On October 22, 2026, all 55 tests passed and the Task 3 verifier accepted the
frozen six-graph Task 2 inputs/caches. It then stopped with
`Stale or incomplete Task 3 context`: the saved Task 3 identity protects older
report checksums, while `report/report.pdf`, sections 04/05/06 and the references
have subsequently changed. This synchronization preserves that evidence rather
than refreshing checksums to imply a new scientific verification. Reconcile the
report-only provenance changes before claiming full Task 3 verification passes.
This does not prevent importing the saved graphs into Gephi.

## Destination setup and first checks

1. Read `AGENTS.md`, `PROJECT_STATUS.md` and this handoff before making changes.
2. Install/configure desktop software or environment packages only with the
   student's approval. Use the `fons-a1` Conda environment for project Python;
   `environment.yml` and `requirements.txt` describe dependencies. Do not copy
   an installed Conda environment between computers.
3. Run `scripts/preflight.ps1` from the cloned root once Conda is configured.
   If Conda is absent from PATH, supply its verified local executable using
   `-CondaExe`; the original host's executable path is not portable.
4. Enable Computer Use on the destination host. First verify an actual Notepad
   screenshot and text input, then a Gephi screenshot, before attempting import
   or layout. Windows 11 success has not yet been established.
5. Import the two saved real graphs into Gephi and verify counts. Record layouts,
   encodings, filtering, tool versions and export settings. Save optional work
   under `results/gephi/` and export SVG/PDF for report use.

For full analytical verification after restoring the ignored inputs/cache, use
the commands in `TASK2_REPRODUCIBILITY.md` and `TASK3_REPRODUCIBILITY.md` with
the destination computer's Conda executable. Do not regenerate assignment models
or recompute expensive distances merely to begin Gephi work.

Commit completed work on one computer and push before pulling on the other.
Review changes before each push. No Submitty submission is authorized by this
GitHub synchronization request.
