import json
import subprocess
from pathlib import Path


def test_legend_generated(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    spec = repo_root / 'pipeline_b' / 'data' / 'figure_spec_legend.json'
    style = repo_root / 'profiles' / 'default_style.json'
    out = tmp_path / 'legend.svg'
    cmd = ["python", str(repo_root / 'pipeline_b' / 'generate_figure_svg.py'), "--spec", str(spec), "--style", str(style), "--out", str(out)]
    subprocess.run(cmd, check=True)
    assert out.exists()
    text = out.read_text()
    # legend should include category labels A, B, C
    assert 'A' in text
    assert 'B' in text
    assert 'C' in text
    # and at least one color hex from the qualitative colormap
    assert '#ffd166' in text or '#1b7a4a' in text
