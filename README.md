# Frontiers of Network Science — Assignment 1

Individual network analysis project for CSCI 4250, Fall 2026.

## First-time setup (Windows with Conda)

Project root: `H:\work_space\Frontiers_of_Network_Science\Assignment_1`.

The local **named Conda environment** `fons-a1` already exists and uses Python 3.12. Start each work session with the following check; it does not create an environment or install packages:

```powershell
Set-Location 'H:\work_space\Frontiers_of_Network_Science\Assignment_1'
& .\scripts\preflight.ps1
```

The preflight verifies Conda environment registration, Python identity, package imports and dependency consistency, required project files/directories, output-directory write access, and a small synthetic calculation/plot export. Temporary probes are removed automatically. It stops on failure. It does not download or analyze real datasets.

The registered local Conda executable is `C:\ProgramData\anaconda3\Scripts\conda.exe`; the local interpreter is `C:\Users\lin\.conda\envs\fons-a1\python.exe`. The wrapper uses Conda from `PATH` if available, otherwise the verified executable. A different verified Conda installation can be supplied with `-CondaExe`. It never changes `PATH`, shell profiles, or execution policy.

For manual validation when `conda` is absent from `PATH`:

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python scripts/check_environment.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python -c "import sys; print(sys.executable)"
```

Only on a new machine, after approval to create an environment or install packages, use `conda env create -f environment.yml` followed by `conda run -n fons-a1 --no-capture-output python -m pip install -r requirements.txt`. Skip creation if the environment exists. Never use system Python or create `.venv` for this project.

To invoke project scripts reliably from fresh agent shells:

```powershell
conda run -n fons-a1 --no-capture-output python src\analyze.py
conda run -n fons-a1 --no-capture-output python -m pytest tests -q
```

The `src/analyze.py` script and production analysis tests are *future* work; do not invoke the analysis script until implemented. Current tests cover environment guards and tiny reference graphs; they do not validate a completed analysis pipeline. When `conda` is absent from `PATH`, replace `conda` in these examples with `& 'C:\ProgramData\anaconda3\Scripts\conda.exe'`. Never guess another installation path or switch interpreters to bypass a failed check.

**VS Code:** use *Python: Select Interpreter* to choose `fons-a1`, then open a fresh integrated terminal. IDE interpreter selection does not guarantee that a separate AI agent shell uses the same interpreter; explicitly use `conda run` for AI execution.

**Work/Codex access:** local desktop sessions can work with the local project only after appropriate permissions; cloud-only work cannot directly use `H:` or the local Conda environment. Codex Local is suitable for local command execution. Agent must inspect whether local terminal access is actually available.

## Create folders

```powershell
New-Item -ItemType Directory -Force -Path data\raw,data\processed,src,tests,results\tables,results\plots,results\gephi,report | Out-Null
```

## Visualization tool check

For a temporary synthetic plot check, choose a new diagnostic subdirectory and run from the project root:

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python scripts/check_visualization.py --output-dir results/plots/visualization-tool-check
```

The script exports diagnostic PNG/PDF files and verification metadata, checks PNG decoding and PDF header/end markers, and leaves them for inspection. It does not generate assignment figures. Render the PDF and inspect both images before treating visual verification as complete. Clean up only the generated diagnostic directory after review. See `PROJECT_STATUS.md` for the verified Gephi installation and current desktop-control limitations.

## Original dataset downloads

- ca-GrQc: https://snap.stanford.edu/data/ca-GrQc.txt.gz
- Power grid: https://public.websites.umich.edu/~mejn/netdata/power.zip

Place the unmodified downloads in `data/raw/`. Do not alter or remove the course's `.docx` or `.pdf` documents. Store the URL and retrieval date; record a checksum when possible.

## Final readiness inspection

Both manually downloaded datasets are present as extracted files under `data/raw/`. Run the read-only audit using:

```powershell
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python scripts/inspect_datasets.py
& 'C:\ProgramData\anaconda3\Scripts\conda.exe' run -n fons-a1 --no-capture-output python -m pytest tests -q
```

The audit records source checksums, archive integrity, raw record/duplicate counts, loaded graph sizes, loops, connectivity and planned model parameters in `results/tables/dataset_preflight.json`. It does not clean inputs, generate assignment models or compute full-network distances. ca-GrQc contains 12 self-loops: decide and document their treatment before production analysis. See `READINESS_PLAN.md` for verified metadata, proposed seeds, statistical conventions, cache invalidation rules, output paths and remaining implementation work. Gephi is treated as manually operated.

## Version control

Public repository: https://github.com/leon-wulin/csci4250-fall2026-assignment-1 . Local branch: `main`; remote: `origin`. The student approved the initial project commit and push on 2026-10-17. Raw archives, extracted data, computational caches and logs are excluded by verified ignore rules. Review each future staged file list before uploading to this public repository.

## Expected project outputs (future)

- `src/`: loading/cleaning, ER and BA generation, exact graph metrics, plot generation.
- `tests/`: hand-verified small graphs + sanity checks.
- `results/tables/`: CSV/JSON metrics and parameters.
- `results/plots/`: distribution figures (four metrics times six networks).
- `results/gephi/`: optional Gephi exports and project files.
- `report/`: report source and final PDF.

Run instructions for analysis scripts must be **added here once the actual scripts exist**. Do not claim any outputs exist until produced and checked.

## Assistant workflow

1. Read `AGENTS.md` (standing rules).
2. Read `PROJECT_STATUS.md` (current progress and parameter registry).
3. Run `& .\scripts\preflight.ps1` and stop if any check fails.
4. Check assignment PDF/DOCX; do one gated task at a time.
5. Run tests and update status with measured results and paths.

## Version reporting

After installing dependencies, record actual tool versions for Task 5:

```powershell
conda run -n fons-a1 --no-capture-output python --version
conda run -n fons-a1 --no-capture-output python -m pip freeze > results\tables\installed_dependencies.txt
conda env export -n fons-a1 --from-history > results\tables\conda_history.yml
```

If using Git, `git init`, `git status` and commits are optional but recommended. Do not push or share the project publicly without approval.

## Submission

Manual submission through Submitty by 2026-10-23 11:59 PM: PDF report, code/supporting files, reproducibility instructions. ZIP supplement if helpful. Review rubric before final submission.
