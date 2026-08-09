# GreenFinance Figure Workflow Prototype

This repository is a lightweight prototype for exploring three small components for academic visualization workflows:

- A JSON-based Design System / Style Profile (profiles/default_style.json)
- Pipeline B: Structured node-edge -> editable SVG generator (pipeline_b/)
- Pipeline A: AI concept illustration experiment scaffold (pipeline_a/)

This prototype intentionally keeps implementation minimal and does NOT reimplement or copy the HypoWeaver backend, renderer, or figure recipes. It is designed for quick experiments and human-reviewed outputs.

Quick start (Unix/Mac):

1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Generate the example SVG (Pipeline B)

```bash
python pipeline_b/generate_svg.py --data pipeline_b/data/sample_graph.json --style profiles/default_style.json --out pipeline_b/examples/sample_diagram_generated.svg
```

3. Run the AI experiment scaffold (Pipeline A) — this is a stub that writes placeholders

```bash
python pipeline_a/generate_images.py --prompts pipeline_a/prompts.yaml --outdir pipeline_a/examples
```

See docs/USAGE.md for more details.


style profile → pipeline_b generator → editable SVG

Pipeline B (pipeline_b/generate_svg.py) consumes the JSON-based style profile at profiles/default_style.json. The generator reads tokens such as:

- colors.background, colors.primary, colors.muted, colors.text
- fonts.label.size
- line.width
- node.default_width, node.default_height, node.rx, node.stroke_width
- canvas.width_px, canvas.height_px

The SVG produced keeps each node and edge in its own <g id="..."> group and embeds metadata in <desc> elements for round-tripping in vector editors (e.g., Inkscape or Illustrator). Edge labels (if present in the input JSON) are rendered near the midpoint of the edge using the annotation font size when available.
