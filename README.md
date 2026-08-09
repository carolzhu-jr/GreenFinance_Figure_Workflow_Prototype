
A minimal data-driven figure grammar layer has been added.

Files:
- profiles/figure_grammar_schema.json : JSON Schema for a tiny figure specification format (data, scales, axes, marks)
- pipeline_b/data/figure_spec_example.json : an example spec that draws a line and points
- pipeline_b/generate_figure_svg.py : a small generator that renders the spec to SVG using style tokens
- tests/test_figure_grammar.py : validates the spec and runs the generator

Usage example:
python pipeline_b/generate_figure_svg.py --spec pipeline_b/data/figure_spec_example.json --style profiles/default_style.json --out pipeline_b/examples/figure_example.svg
