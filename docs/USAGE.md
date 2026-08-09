# Usage

This file shows basic commands to run the two prototype pipelines.

Pipeline B: Structured node-edge -> SVG

```bash
python pipeline_b/generate_svg.py --data pipeline_b/data/sample_graph.json --style profiles/default_style.json --out pipeline_b/examples/sample_diagram_generated.svg
```

Pipeline A: AI concept illustration scaffold (stub)

```bash
python pipeline_a/generate_images.py --prompts pipeline_a/prompts.yaml --outdir pipeline_a/examples
```

Notes:
- Pipeline A is a human-reviewed experiment scaffold. It writes images and metadata but does not claim scientific validity.
- Pipeline B uses authoritative node-edge JSON as input and preserves node/edge metadata in the output SVG so it remains editable.
