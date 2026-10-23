# Power Grid figure reproduction

## Files and roles

- `../../data/processed/task2/power_real.graphml`: frozen analyzed topology, 4941 nodes/6594 edges, undirected/unweighted.
- `power_real.gml`: import copy with original numeric IDs and all nodes retained.
- `power_grid_layout_base.svg`: immutable student-exported Gephi 0.11.3 Yifan Hu layout, including realized coordinates. This is the coordinate source for exact figure reproduction; interactive layout reruns need not reproduce identical coordinates.
- `../../scripts/style_power_grid_svg.ps1`: recomputes degree from GraphML, preserves the export's edge paths and node centers, adds vector styling and annotations. Produces `power_grid_annotated_draft.svg` and `power_grid_style_audit.json`.
- `../../scripts/export_power_grid_pdf.mjs`: exports the known generated SVG subset as PDF vector drawing primitives and copies the annotated SVG to `power_grid_final.svg`. Produces `power_grid_final.pdf` (report figure). PDF uses larger labels and a compact legend rather than the standalone SVG poster header/footer.
- `power_grid_final.png`: reviewed raster rendering of the final PDF; PDF/SVG remain vector originals.
- `../../report/sections/07_visualization_optional.tex`: figure inclusion, caption, source citation and methods. Other assignment sections unchanged.
- `power_grid_file_manifest.json`: checksums for inputs, scripts, final outputs and LaTeX section; runtime versions are recorded alongside it.

## Layout and styling

Gephi 0.11.3, Yifan Hu: optimal distance 100; relative strength 0.2; initial step 20; step ratio 0.95; adaptive cooling enabled; convergence threshold 0.0001. No filtering, aggregation, or geographic positioning. There is no saved `.gephi` project yet; the coordinate-bearing SVG is preserved.

The final SVG is a 1600 x 1680 white canvas. Radius is `1.5 + 4.5*sqrt((k-1)/18)` display units; RGB is `(72-47*t,143-78*t,183-67*t)`, with `t=(k-1)/18`, rounded to integers. Degree range is 1-19. Edges are straight gray #82909f, opacity 0.25, stroke width 0.55 in final source-canvas units. PDF applies a uniform half-scale transformation and excludes the poster title/footer in favor of LaTeX caption and its own compact legend. PDF callouts use 11-point Helvetica. The six highest-degree nodes are labeled, breaking ties by numeric ID: 2553 (19), 4458 (18), 831 (14), 3468 (14), 4345 (14), 2382 (13).

No node is identified as a named facility. Size/color do not encode capacity, flow, geographic region or failure criticality. Blue intensity and size redundantly encode degree to support visual reading. The full graph remains present.

## Run from the project root

No Python or new package installation is required. Use a normal PowerShell shell that permits local scripts:

```powershell
& .\scripts\style_power_grid_svg.ps1
node .\scripts\export_power_grid_pdf.mjs '<node_modules directory containing pdf-lib>'
node .\scripts\render_power_grid_preview.mjs '<node_modules directory containing pdfjs-dist and @napi-rs/canvas>'
```

This machine used the already bundled runtime:

```powershell
& 'C:\Users\lin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' .\scripts\export_power_grid_pdf.mjs 'C:\Users\lin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
```

`pdf-lib` is the only package needed for vector PDF generation. Node.js must support `import.meta.dirname`. Run the styling script first, then PDF export. These scripts intentionally regenerate derived final/draft outputs; preserve manual edits elsewhere. Keep the original GraphML and layout-base SVG unchanged. Bitwise PDF identity is not guaranteed because PDF metadata can include generation timestamps; node/edge sets, positions, encodings and labels are the reproducibility target.

For report compilation on the main computer with its existing LaTeX distribution:

```powershell
& .\report\build_report.ps1
# Or pass -PdfLatexPath with a verified pdflatex executable.
```

The local visualization host has no located LaTeX compiler. Therefore `report/report.pdf` has not been rebuilt here. The independent figure PDF was generated, parsed and rendered for review; final whole-report compilation, citation/float placement and printed-size inspection remain required on the LaTeX host. Do not treat the preexisting report PDF as containing this new figure.

## Validation performed

- Original SVG XML parsed: 4941 network circles, 6594 edge paths.
- Restyled SVG retained all original edge path strings/classes and numeric node IDs; original source file preserved.
- PDF exporter requires exactly 4941 nodes and 6594 edges before saving, and uses vector line/circle/text primitives rather than a raster image.
- Rendered the one-page PDF and visually checked full-network bounds, six labels and legend.
- Existing numerical results and original course documents were not changed. The optional task remains incomplete until ca-GrQc is finished and the student reviews the report.
