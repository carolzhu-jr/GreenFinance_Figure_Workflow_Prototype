import json
import subprocess
from pathlib import Path


def test_panels_generate(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    spec = repo_root / 'pipeline_b' / 'data' / 'figure_spec_panels.json'
    style = repo_root / 'profiles' / 'default_style.json'
    out = tmp_path / 'panels.svg'
    cmd = ["python", str(repo_root / 'pipeline_b' / 'generate_figure_svg.py'), "--spec", str(spec), "--style", str(style), "--out", str(out)]
    subprocess.run(cmd, check=True)
    assert out.exists()
    text = out.read_text()
    # check that both panel titles are present
    assert 'Series A' in text
    assert 'Series B' in text
