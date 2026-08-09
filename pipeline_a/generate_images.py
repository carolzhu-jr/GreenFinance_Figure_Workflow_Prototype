#!/usr/bin/env python3
"""
Skeleton: read prompts.yaml, for each prompt call an image API (or stub), save images and metadata.
Always save a JSON metadata log (prompt, model params, timestamp, human_judgement placeholder).
"""
import yaml, json, argparse, time, os
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default="prompts.yaml")
    ap.add_argument("--outdir", default="examples")
    args = ap.parse_args()
    data = yaml.safe_load(Path(args.prompts).read_text())
    os.makedirs(args.outdir, exist_ok=True)
    for item in data:
        # Here you would call an image API. In the prototype we write a stub file.
        img_path = Path(args.outdir)/(item['id'] + ".png")
        # stub: create a tiny placeholder file
        with open(img_path, "wb") as f:
            f.write(b"")  # replace with real image bytes
        metadata = {
            "id": item['id'],
            "prompt": item['prompt'],
            "model": item.get('model'),
            "seed": item.get('seed'),
            "timestamp": time.time(),
            "note": item.get('notes'),
            "image_path": str(img_path)
        }
        Path(args.outdir)/(item['id'] + ".json")
        Path(args.outdir)/(item['id'] + ".json").write_text(json.dumps(metadata, indent=2))
        print("Wrote", img_path, "and metadata")

if __name__ == "__main__":
    main()
