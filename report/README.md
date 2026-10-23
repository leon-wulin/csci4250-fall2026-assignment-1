# Assignment 1 LaTeX report

This is an editable English-language report scaffold, **not** a finished analysis or answer.

## Add it to the existing project

Copy the `report/` directory into the current `Assignment 1/` folder (merge, do not delete existing files). Do not replace your top-level `AGENTS.md` or `PROJECT_STATUS.md`.

Confirmed local project root: `H:\work_space\Frontiers_of_Network_Science\Assignment_1`. This LaTeX tree is the official editable report source. Preserve the section contents; replace placeholders only after the corresponding analysis has been verified.

## Windows requirements

- MiKTeX is already installed locally. Do not reinstall it. The build script disables automatic package installation; missing packages must be reviewed and approved separately.
- Optional: Visual Studio Code extension **LaTeX Workshop** for editing and previewing.
- No Python or Conda changes are necessary to compile the LaTeX report.

Verify MiKTeX by opening a **new** terminal and running: `pdflatex --version`.

Note: LaTeX Workshop's default `latexmk` recipe may require Perl with MiKTeX. Use the included `build_report.ps1` or `pdflatex` commands instead; Perl is **not** needed for this template.

## Build

From the project root in Windows PowerShell:

```powershell
.\report\build_report.ps1
```

If the current terminal does not have MiKTeX on PATH, use the verified local executable without changing the system PATH:

```powershell
.\report\build_report.ps1 -PdfLatexPath 'C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe'
```

The script runs pdfLaTeX twice with package auto-installation and shell-command execution disabled. Intermediate files and validation backups stay in `report/build/`, which is ignored by Git; `report/report.pdf` remains the reviewable draft output. Actual compiler versions and diagnostics are recorded in `PROJECT_STATUS.md`.

Setup verified on 2026-10-17: missing support packages were installed with the student's approval, the two-pass local build succeeded, and all five PDF pages were rendered and visually checked. `report.pdf` is now a locally generated placeholder draft. The script uses a separate executable and argument list for reliable Windows paths. The placeholder macro has local line wrapping; section text and all uncomputed tables remain unchanged. The nonfatal epstopdf shell-execution warning does not affect PDF-figure inclusion.

Approved support packages installed: `kvsetkeys`, `kvdefinekeys`, `pdfescape`, `hycolor`, `stringenc`, `kvoptions`, `intcalc`, `bitset`, `rerunfilecheck`, `refcount`, `gettitlestring`, `ltxcmds`, `infwarerr`, `bigintcalc`, `uniquecounter`. They do not need to be reinstalled on this machine. See `../PROJECT_STATUS.md` for the build history and disclosed earlier package-lookup side effect. Do not use MiKTeX's `kpsewhich` lookup as an assumed read-only audit: this installation can auto-install during lookup. Review and approve any genuinely new dependency before installing it, then rerun the installer-disabled build.

Or directly:

```powershell
cd report
New-Item -ItemType Directory -Path build -Force | Out-Null
pdflatex -disable-installer -disable-write18 -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdflatex -disable-installer -disable-write18 -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
Copy-Item build/main.pdf report.pdf
```

The generated `report/report.pdf` is the submission-format draft; it is not ready for submission until all placeholders are replaced and all results are checked.

## Where to write answers

`main.tex` handles packages, title, ordering and table of contents. Add content in:

- `sections/01_real_networks.tex` — Task 1
- `sections/02_model_generation.tex` — model-generation prerequisite
- `sections/03_global_properties.tex` — Task 2
- `sections/04_distributions.tex` — Task 3
- `sections/05_comparison.tex` — Task 4
- `sections/06_methodology.tex` — Task 5
- `sections/07_visualization_optional.tex` — bonus
- `sections/references.tex` — sources

Replace the visible `[To complete: ...]` placeholders with verified content. `\missing` in tables means "not computed yet," not zero. Avoid inventing measurements. Add `\cite{snap-ca-grqc}` or `\cite{newman-power-grid}` wherever you use the respective dataset source.

## Figures

Place machine-generated PDF figures in `results/plots/` in the project root, and exported Gephi PDFs in `results/gephi/`. The document `\graphicspath` includes both locations.

For example, in the Task 3 section:

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{degree_distribution.pdf}
  \caption{Degree distributions for the six networks.}
  \label{fig:degree}
\end{figure}
```

If using SVG from Gephi, also export PDF for simple inclusion in pdfLaTeX. Keep original SVG for the extra-credit submission.

## Codex workflow

1. Read top-level `AGENTS.md` and `PROJECT_STATUS.md` before editing.
2. Edit only the targeted report section. Never replace measured results with assumptions.
3. Keep figures in `results/`, source code in `src/`, and report text in `report/`.
4. Run the PDF build after modifications, inspect the output, and record any errors.
5. Verify every figure reference, number, label, citation and assignment requirement before saying the task is complete.
6. Update `PROJECT_STATUS.md` with what changed and the next action.
