import subprocess
from pathlib import Path

def test_generate_svg(tmp_path):
    out = tmp_path / "out.svg"
    cmd = ["python", "pipeline_b/generate_svg.py", "--data", "pipeline_b/data/sample_graph.json", "--style", "profiles/default_style.json", "--out", str(out)]
    res = subprocess.run(cmd, check=True)
    assert out.exists()
    text = out.read_text()
    assert '<g id="node-n1"' in text
