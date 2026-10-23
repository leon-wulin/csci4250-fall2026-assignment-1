# Main-host handoff: optional figures

Both network figures are integrated into `report/sections/07_visualization_optional.tex`. Main report PDF has NOT been rebuilt on the visualization host; the existing `report/report.pdf` is stale with respect to these figures.

1. Pull this commit on the main computer after preserving any local changes. Do not overwrite newer analytical/report work.
2. Review `power_grid_final.pdf` and `grqc_final.pdf`, including captions, numeric IDs, degree legends and community keys. Independent PNG previews are provided. Both figures retain complete analyzed topology.
3. Use the existing local LaTeX distribution: `& .\report\build_report.ps1` (or verified `-PdfLatexPath`). Check figure placement, printed-size typography, cross references, bibliography and overflow. The report still has unrelated draft placeholders (including student name); perform final report-wide review.
4. Reproduction: follow `POWER_GRID_REPRODUCIBILITY.md` and `GRQC_REPRODUCIBILITY.md`. Frozen coordinate SVGs, saved `.gephi`, derived scene/audit JSON, styling/export scripts, manifests and tool versions are included. No need to recompute Tasks 2/3 just to rebuild figures.
5. The saved Gephi project captures both workspaces at the student-save point. Final report styling is performed by the scripts after export; use final PDF/SVG outputs, not screenshots. Randomized community/layout reruns can differ; preserve the saved realization.
6. Review all assignment requirements and reproduction files, then assemble the submission package. Student approval and manual Submitty submission remain required. Nothing has been submitted automatically.

No LaTeX compiler or new packages were installed on the visualization host. Original dataset files, analytical tables and original course documents were not changed. `.codex`, caches, logs and raw downloads are excluded from Git.
