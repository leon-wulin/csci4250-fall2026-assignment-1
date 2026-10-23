# Main-host handoff: optional figures

Main-host update (2026-10-23): both figures have now been compiled into the complete `report/report.pdf` review draft. The PDF has 16 pages: optional methods on page 13, ca-GrQc Figure 9 on page 14, Power Grid Figure 10 on page 15, and references on page 16. Its SHA-256 is `0affd3e72b14b524e3467e47f0d166b8e97fe93d6caeecf3cec3b7a58ccb7038`. All pages were rendered and checked; 26 Gephi file hashes and 55 tests passed. Student/advisor revisions, including the student-name placeholder, remain pending. The notes below describe the original visualization-host handoff and remain useful when rebuilding after revisions.

1. Pull this commit on the main computer after preserving any local changes. Do not overwrite newer analytical/report work.
2. Review `power_grid_final.pdf` and `grqc_final.pdf`, including captions, numeric IDs, degree legends and community keys. Independent PNG previews are provided. Both figures retain complete analyzed topology.
3. Use the existing local LaTeX distribution: `& .\report\build_report.ps1` (or verified `-PdfLatexPath`). Check figure placement, printed-size typography, cross references, bibliography and overflow. The report still has unrelated draft placeholders (including student name); perform final report-wide review.
4. Reproduction: follow `POWER_GRID_REPRODUCIBILITY.md` and `GRQC_REPRODUCIBILITY.md`. Frozen coordinate SVGs, saved `.gephi`, derived scene/audit JSON, styling/export scripts, manifests and tool versions are included. No need to recompute Tasks 2/3 just to rebuild figures.
5. The saved Gephi project captures both workspaces at the student-save point. Final report styling is performed by the scripts after export; use final PDF/SVG outputs, not screenshots. Randomized community/layout reruns can differ; preserve the saved realization.
6. Review all assignment requirements and reproduction files, then assemble the submission package. Student approval and manual Submitty submission remain required. Nothing has been submitted automatically.

No LaTeX compiler or new packages were installed on the visualization host. Original dataset files, analytical tables and original course documents were not changed. `.codex`, caches, logs and raw downloads are excluded from Git.
