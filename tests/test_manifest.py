import json
from pathlib import Path
import subprocess


def test_manifest_contains_keys(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    spec = repo_root / 'pipeline_b' / 'data' / 'figure_spec_example.json'
    style = repo_root / 'profiles' / 'default_style.json'
    out = tmp_path / 'figure.svg'
    cmd = ["python", str(repo_root / 'pipeline_b' / 'generate_figure_svg.py'), "--spec", str(spec), "--style", str(style), "--out", str(out)]
    subprocess.run(cmd, check=True)
    manifest = tmp_path / 'figure.svg.meta.json'
    assert manifest.exists()
    m = json.loads(manifest.read_text())
    # required keys
    for k in ['spec_path', 'style_path', 'style_name', 'style_version', 'generator', 'timestamp', 'artifact', 'commit_sha']:
        assert k in m
    # artifact path should exist
    art_path = Path(m['artifact']['path'])
    assert art_path.exists()
    # sha256 should match actual file
    import hashlib
    actual = hashlib.sha256(art_path.read_bytes()).hexdigest()
    assert m['artifact']['sha256'] == actual
