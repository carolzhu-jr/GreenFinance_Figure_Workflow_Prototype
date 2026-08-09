import json
import subprocess
from pathlib import Path

def test_generate_svg_uses_style(tmp_path):
    # Prepare a temporary style file by copying the default and modifying node stroke
    repo_root = Path(__file__).resolve().parent.parent
    default_style = repo_root / 'profiles' / 'default_style.json'
    style_copy = tmp_path / 'style.json'
    s = json.loads(default_style.read_text())
    # change node stroke color to a distinctive value
    s['node']['stroke'] = '#ff00ff'
    style_copy.write_text(json.dumps(s))

    out_svg = tmp_path / 'out.svg'
    cmd = ["python", str(repo_root / 'pipeline_b' / 'generate_svg.py'), "--data", str(repo_root / 'pipeline_b' / 'data' / 'sample_graph.json'), "--style", str(style_copy), "--out", str(out_svg)]
    subprocess.run(cmd, check=True)
    assert out_svg.exists()
    text = out_svg.read_text()
    # The node rect stroke should reflect the new color
    assert '#ff00ff' in text
