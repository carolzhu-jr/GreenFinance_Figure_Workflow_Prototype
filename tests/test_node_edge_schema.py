import json
from jsonschema import validate
import subprocess
from pathlib import Path

SCHEMA = Path('profiles/node_edge_schema.json')
SAMPLE = Path('pipeline_b/data/sample_graph.json')
GEN = Path('pipeline_b/generate_svg.py')


def test_sample_matches_schema():
    schema = json.loads(SCHEMA.read_text())
    sample = json.loads(SAMPLE.read_text())
    validate(instance=sample, schema=schema)


def test_generator_produces_svg(tmp_path):
    out = tmp_path / 'out.svg'
    cmd = ["python", str(GEN), "--data", str(SAMPLE), "--style", "profiles/default_style.json", "--out", str(out)]
    subprocess.run(cmd, check=True)
    assert out.exists()
    text = out.read_text()
    # Check that node metadata and edge metadata appear in the SVG
    assert '"role": "process"' in text or '"role": "data"' in text
    assert '"id": "e2"' in text or '"id": "e3"' in text
