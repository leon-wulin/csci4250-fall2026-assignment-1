# Gephi preparation

Open `power_real.gml` or `grqc_real.gml` with Gephi File > Open, and import as undirected. These files preserve the frozen analyzed GraphML topology, including isolated nodes. Numeric labels are original dataset node IDs, not author or facility names. No layout, filtering, inferred geographic coordinates, or community assignments have been added.

| File | Nodes | Edges |
|---|---:|---:|
| power_real.gml | 4941 | 6594 |
| grqc_real.gml | 5242 | 14484 |

The ca-GrQc analyzed copy excludes the 12 self-loops previously approved for removal; the original source metadata reports 14496 edges. These exports are not copies of the unavailable raw archives. Original GraphML files are unchanged.

Conversion: `scripts/export_gephi_gml.ps1` uses PowerShell/.NET XML parsing, writes ASCII GML and checks complete node/undirected-edge sets after re-reading its output. It refuses to overwrite existing GML files. SHA-256 values and validation results are in `gml_conversion_audit.json`. No Python environment or package installation is needed for this format conversion. Gephi import is pending student confirmation.

For subsequent desktop tests, maximize Gephi before interacting. Open the file manually, confirm the import counts above, then continue layout and selective-label experiments. Formal figures still need documented layout settings, meaningful encodings, legends and SVG/PDF exports.
