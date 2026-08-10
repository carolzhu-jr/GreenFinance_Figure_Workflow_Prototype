# GreenFinance Figure Workflow Prototype — Research Overview

This repository is a lightweight research prototype exploring data-driven, editable figure generation for academic visualization workflows. It is intentionally minimal: the goal is to experiment with reproducible figure specifications, style profiles, lightweight rendering to editable SVG, and provenance that supports research reproducibility — not to recreate large plotting systems or the HypoWeaver backend.

This README provides a concise, research-oriented overview: motivation, architecture, current capabilities, supported workflow, a publication-style multi-panel demo spec you can run, limitations, and recommended future directions.

---

Motivation

- Reproducible figures: capture the mapping from data → visual encodings as machine-readable specs so figures can be regenerated exactly and audited.
- Editable outputs: produce SVG that designers and reviewers can edit (Inkscape, Illustrator) while preserving structured metadata to allow round-tripping edits back to structured data.
- Lightweight experimentation: provide small, composable primitives (style profiles, node-edge diagrams, and a minimal figure grammar) researchers can extend without reengineering existing renderers.

Audience

- Researchers building reproducible visualization pipelines
- Designers who iterate on programmatic figures in vector editors
- Teams exploring human-AI-assisted illustration while retaining provenance and style control

---

High-level architecture (conceptual)

Repository components (what's included)

- profiles/
  - default_style.json — human-editable style profile (colors, fonts, canvas, line, grid, legends, colormaps)
  - schema.json — JSON Schema for style tokens
  - node_edge_schema.json — schema for node/edge diagrams
  - figure_grammar_schema.json — schema for the minimal figure grammar

- pipeline_b/
  - generate_svg.py — node-edge → editable SVG generator (diagram pipeline)
  - generate_figure_svg.py — minimal data-driven figure grammar renderer (marks, scales, axes, legends, panels)
  - data/ — example specs: sample_graph.json, figure_spec_example.json, figure_spec_legend.json, figure_spec_panels.json, figure_spec_publication_demo.json

- tests/ — small tests validating schemas, generation, and manifest/provenance outputs

Conceptual flow

  data (CSV/JSON)  -->  figure spec (JSON)  -->  generator (uses style profile)  -->  editable SVG + manifest
                                     ^                                            |
                                     |--------------------------------------------|

- Style profile centrally controls visual tokens (colors, sizes, fonts, colormaps).
- The generator emits a companion .meta.json manifest (spec path, style used, generator version, commit SHA, artifact size & sha256) to support reproducibility and archival.

---

Current capabilities (lightweight list)

- Style profiles
  - Human-editable JSON token set (colors, colormaps, fonts, canvas, line widths, plot tokens).
  - Schema validation for the style profile.

- Node-edge diagrams (pipeline_b/generate_svg.py)
  - JSON schema for nodes & edges (shapes, sizes, roles, waypoints, arrowheads, metadata).
  - Generator outputs layered SVG with groups: layer-background, layer-edges, layer-nodes, layer-annotations and per-element <desc> JSON for round-tripping.

- Minimal figure grammar (pipeline_b/generate_figure_svg.py)
  - Small schema supporting: data blocks, scales (linear), axes (bottom/left), marks: line, point, bar.
  - Lightweight categorical legends (color-by-field) that reuse style.colormaps.
  - Panels: explicit grid layout (rows × cols), panel-local scales and per-panel marks, panel titles.
  - Outputs layered SVG and a companion manifest (.meta.json) with provenance (spec, style, generator version, commit SHA, artifact checksum).

- Tests
  - JSON Schema validation for specs
  - Smoke tests that guarantee generators run and produce SVG + correct manifest metadata

---

Supported workflow (recommended minimal loop)

1. Create or edit a style profile
   - Edit `profiles/default_style.json` to set color tokens, colormaps, fonts, and canvas settings.

2. Create a small figure spec
   - Use the figure grammar (see examples in `pipeline_b/data/`) to describe datasets, scales, marks, and optional panels.
   - Example specs are: `figure_spec_example.json`, `figure_spec_legend.json`, `figure_spec_panels.json`, and `figure_spec_publication_demo.json` (demo below).

3. Generate an editable SVG and manifest
   - Run:
     ```bash
     python pipeline_b/generate_figure_svg.py --spec pipeline_b/data/figure_spec_publication_demo.json --style profiles/default_style.json --out pipeline_b/examples/publication_demo.svg
     ```
   - This produces the SVG plus `pipeline_b/examples/publication_demo.svg.meta.json` containing provenance and artifact checksums.

4. Edit SVG in a vector editor
   - Open the generated SVG in Inkscape/Illustrator. Each logical element (panels, marks, legend, annotations) lives in named layers. Per-element metadata is stored in <desc> elements for potential round-tripping.

5. Archive and reproduce
   - Store the generated SVG and its `.meta.json` alongside the spec and style profile to enable exact reproduction (the manifest includes generator version and Git commit SHA if available).

---

Publication-style multi-panel demo (run this to reproduce a demo figure)

We include a publication-style demo specification that shows a 2×2 multi-panel layout with small panel titles and consistent styling. The spec is `pipeline_b/data/figure_spec_publication_demo.json`.

To render the demo:

1. Make sure dependencies are installed (svgwrite, jsonschema for tests):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

2. Run generator:

```bash
python pipeline_b/generate_figure_svg.py --spec pipeline_b/data/figure_spec_publication_demo.json --style profiles/default_style.json --out pipeline_b/examples/publication_demo.svg
```

3. Inspect results:
- The SVG will be in `pipeline_b/examples/publication_demo.svg` (create the `examples/` directory if it does not exist). The manifest will be `pipeline_b/examples/publication_demo.svg.meta.json`.
- Open the SVG in a vector editor to check panel titles, axes, marks, legends, and to perform final visual polishing.

(See the included spec file for the content used to produce this demo.)

---

Limitations (explicit and intentional)

- Not a plotting library: this prototype implements a minimal subset of a figure grammar. It targets reproducible, editable outputs rather than full-featured statistical plotting.
- Scales: only basic linear scales are reliably implemented. Ordinal and continuous colorbars are intentionally minimal or unimplemented.
- Axes: tick formatting, label rotation, gridlines, and spacing are basic. For publication-quality typography and spacing you should post-edit the SVG or extend the generator.
- Legends: currently supports categorical color legends only. No continuous colorbars or shape/size legends.
- Panels: explicit grid layout with explicit panel entries. There is no automatic faceting or data-driven panel generation.
- Round-tripping: per-element <desc> metadata is embedded but a complete automated re-import pipeline is not provided here.

---

Future directions (research opportunities)

- Expand the minimal figure grammar to include scales (log/symlog), more marks (area/violin/heatmap), and simple statistical aggregations.
- Add shared vs. independent scale options for panels and automatic faceting constructs.
- Implement JSON-LD-based metadata for richer provenance and better tool interoperability.
- Add a small re-import helper that reads edits from SVG (positions) back into spec JSON for iterative design.
- Integrate Pipeline A (AI-assisted illustration) outputs with style + provenance tracking for human-in-loop illustration selection.

---

Contributing and reproducibility notes

- This repository is intentionally small and permissive for experimentation. Changes that add major dependencies or recreate large plotting stacks are discouraged; prefer small, testable, data-first additions.
- For reproducibility, always commit `profiles/default_style.json` and the spec you used alongside the generated SVG and its `.meta.json` manifest.

License

- This project is published under the MIT license (see LICENSE file if present).

---

Contact

- Repo owner: carolzhu-jr (GitHub)
- For research collaboration or questions about the prototype, open an issue or PR with reproducible examples and expectations.
