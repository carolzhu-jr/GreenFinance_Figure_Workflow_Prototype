import json
from jsonschema import validate
import subprocess
from pathlib import Path

SCHEMA = Path('profiles/figure_grammar_schema.json')
SPEC = Path('pipeline_b/data/figure_spec_example.json')
GEN = Path('pipeline_b/generate_figure_svg.py')


def test_spec_matches_schema():
    schema = json.loads(SCHEMA.read_text())
    spec = json.loads(SPEC.read_text())
    validate(instance=spec, schema=schema)


def test_figure_generator_runs(tmp_path):
    out = tmp_path / 'figure.svg'
    cmd = ["python", str(GEN), "--spec", str(SPEC), "--style", "profiles/default_style.json", "--out", str(out)]
    subprocess.run(cmd, check=True)
    assert out.exists()
    text = out.read_text()
    assert '<polyline' in text or '<circle' in text or '<rect' in text
