# Optional network figure plan

Status: proposed design, 2026-10-22; no final figures or community results yet.

## Deliverables

Two real-network vector figures, one per dataset, plus editable Gephi project(s), exported SVG/PDF, PNG review copies and recorded settings. Required Task 3 distributions remain separate and unchanged.

1. ca-GrQc: full analyzed network (5242 nodes, 14484 edges), ForceAtlas 2 layout, degree-based node size, categorical modularity-community colors. Preserve disconnected components and isolates. Begin with all nodes; if component packing makes the main structure unreadable, use an explicitly labeled LCC detail plus whole-network inset rather than silently discarding components. Any LCC view must state its actual node and edge counts.
2. Western States Power Grid: full analyzed network (4941 nodes, 6594 edges), Yifan Hu layout, degree-based node size, uniform blue nodes and light gray edges. This is a topological drawing, not a geographic map. No physical coordinates, capacity, flow or engineering-criticality interpretation is supported by these inputs.

## Initial style settings (starting points, not verified final choices)

- White background; fine gray, unweighted, undirected edges; no arrowheads.
- Degree-based node diameter range approximately 2-10 display units, adjusted after preview. Record the actual mapping; do not imply circle area is proportional to degree when using linear diameter ranking.
- ca-GrQc categorical palette: use visually distinguishable colors. If there are too many communities for a usable legend, use distinct colors for a documented set of largest communities and gray for the rest; retain every node. Community IDs are algorithmic categories, not named scientific fields.
- Start with edge opacity 10-20% for ca-GrQc and 20-35% for Power Grid, subject to readability in vector export.
- Label at most 5-10 highest-degree nodes per network, with a deterministic ID-based tie-break. Labels are source numeric IDs, not author/facility names. A prepared selective-label input is preferable to enabling thousands of labels. If labels add no useful information, use sparse callouts and explain this choice.
- Legends must include node-size examples with real degree values; ca-GrQc also needs community color keys. Captions state N/M, layout, scope and label selection. Add title/legend in a separate vector composition step if Gephi's built-in preview cannot place them reliably.

## Gephi workflow without Data Laboratory

1. Maximize the window; verify workspace and Context counts. Save an editable project under results/gephi with a new filename.
2. Statistics > Average Degree: run if Degree is absent from Appearance ranking. Appearance > Nodes > Size > Ranking > Degree: select range and Apply.
3. For ca-GrQc, Statistics > Modularity: use undirected/unweighted input, resolution 1.0 as an initial choice; record all actual options, randomization behavior, Q and community count. Appearance > Nodes > Color > Partition > Modularity Class: apply palette. This computation is for figure encoding and does not replace saved assignment statistics.
4. ca-GrQc: ForceAtlas 2 trial, record scaling/gravity, LinLog, overlap prevention, approximation and thread settings; stop once the view is stable enough for inspection. Then use Noverlap if needed. Power Grid: Yifan Hu trial, record optimal distance, relative strength, step settings and cooling; use Noverlap if needed. Fit graph to viewport. Existing trials are exploratory, not final reproducible layouts.
5. Use prepared sparse labels; test their visibility in Preview. Preview > Refresh after changes. Adjust node borders, label font and edge opacity/thickness against final page size.
6. Export SVG and PDF; produce PNG review copy. Preserve layout coordinates in the Gephi project. Do not assume rerunning a force-directed layout produces identical coordinates.
7. Check at intended print size: no clipped nodes, readable legends, restrained labels, visible edges, correct counts and no unsupported semantic claims. Record any filtering and all final settings before report integration.

## Next smallest action

Complete one Power Grid proof figure with degree sizing, finished layout and a Preview export. Review it before applying the finalized workflow to ca-GrQc. Automatic desktop operation and student manual operation can follow the same checklist.
