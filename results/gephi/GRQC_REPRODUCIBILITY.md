# ca-GrQc final figure reproduction

Inputs: frozen `data/processed/task2/grqc_real.graphml`, student-exported `grqc_layout_base.svg` and saved `network_visualizations.gephi`. Originals are preserved. Gephi ZIP entries are read without changing the project. Workspace_2 is the ca-GrQc workspace; its appearance XML maps eight RGB values to actual modularity class IDs. Other nodes remain collectively gray; their individual class IDs are retained in the project, not reconstructed from gray color.

Run from project root with PowerShell and Node.js (this session used Node 24.22.1, pdf-lib 1.17.1 and sharp 0.35.5; no packages installed):

```powershell
& .\scripts\prepare_grqc_figure.ps1
node .\scripts\render_grqc_figure.mjs '<node_modules directory containing pdf-lib and sharp>'
node .\scripts\render_power_grid_preview.mjs '<node_modules directory containing pdfjs-dist and @napi-rs/canvas>' grqc_final
```

The existing bundled module directory on this host is `C:\Users\lin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules`; bundled Node executable is under the adjacent `node/bin/node.exe`. No Python is used. PowerShell execution requires a shell permitted to execute local scripts; do not change system policy as part of reproduction.

The preparation script verifies all 5242 original node IDs and every one of 14484 undirected edge endpoint pairs against frozen GraphML, including the isolated node. It outputs `grqc_figure_scene.json`, containing realized coordinates, original colors, selected-community assignments, recomputed degrees and edge pairs. This file plus saved project preserves realized results when randomized Gephi reruns differ.

Gephi 0.11.3 ForceAtlas 2: scaling 100, stronger gravity on, gravity 1, Barnes-Hut enabled, theta 1.2, jitter tolerance 1, 15 threads, edge weight influence 1; LinLog, dissuade hubs and prevent overlap off. Manually stopped at displayed iteration 103685, not a convergence certificate. Modularity: randomization on, weights off, resolution 1, class IDs start 0; displayed Q=0.857, 390 communities. Earlier randomization-off calculation was cancelled and its partial report must not be used.

Selected classes and measured SVG membership counts: 223=295, 18=273, 35=243, 142=235, 202=226, 297=197, 301=180, 146=158; remaining 3435 nodes gray. Selected original colors map uniquely to these classes through saved appearance XML. Final categorical colors and labels are in `grqc_style_audit.json`.

Final SVG/PDF: affine fit of all existing node coordinates to 1600 x 1640 canvas; PDF uses half scale. Circle radius is `1.4+5*sqrt(k/81)` canvas units. Edges join original endpoint nodes, straight gray #88949e, opacity .18, width .65. Six highest-degree nodes are labeled (numeric ID breaks ties), with callout leaders and white text backing. Node-size examples and community legend are explicit. Layout/size/color do not identify research fields or people by name. No vertices/edges filtered or aggregated. The PDF is drawn with vector circles/lines/text, not rasterized.

Outputs: `grqc_final.svg`, `grqc_final.pdf`, `grqc_final.png` (SVG review), `grqc_final_pdf_review.png` (independent PDF review), scene/audit JSON and checksum manifest. Scripts regenerate derived outputs. Coordinate-bearing SVG and saved Gephi project are essential source artifacts. PDF metadata timestamps can differ across reruns; visual/structural reproduction is the target.

LaTeX inclusion, source citation, caption and methods are in `report/sections/07_visualization_optional.tex`. No local LaTeX compiler was found in this session: existing `report/report.pdf` remains stale. On the main LaTeX computer run `report/build_report.ps1`, then check figure/caption sizing, cross-references and page layout. No submission or publication is authorized by these records.
