#!/usr/bin/env python3
"""
Tiny generator that reads nodes/edges JSON and a style JSON and emits an editable SVG.
Each node is a <g id="node-<id>"> and each edge is a <g id="edge-<id>">. Metadata is stored in <desc>.
"""
import json
import argparse
from pathlib import Path
import svgwrite


def load_json(p):
    return json.loads(Path(p).read_text())


def node_group(dwg, node, style):
    # Create a group positioned at node coordinates. Rect centered at (0,0) within group.
    nid = node['id']
    label = node.get('label', nid)
    w = style['node'].get('default_width', 120)
    h = style['node'].get('default_height', 36)
    rx = style['node'].get('rx', 4)
    fill = style['node'].get('fill', style['colors'].get('background', '#fff'))
    stroke = style['node'].get('stroke', style['colors'].get('primary', '#000'))
    stroke_w = style['node'].get('stroke_width', 1)
    font_size = style['fonts']['label']['size']

    g = dwg.g(id=f"node-{nid}", class_="node", transform=f"translate({node['x']},{node['y']})")
    rect = dwg.rect(insert=(-w/2, -h/2), size=(w, h), rx=rx, fill=fill, stroke=stroke, stroke_width=stroke_w)
    g.add(rect)
    text = dwg.text(label, insert=(-w/2 + 10, 6), fill=style['colors'].get('text', '#111'), font_size=font_size)
    g.add(text)
    # Embed metadata in a desc element for round-tripping
    g.add(dwg.desc(json.dumps({'id': nid, 'label': label})))
    return g


def edge_group(dwg, eid, src, tgt, style):
    g = dwg.g(id=f"edge-{eid}", class_='edge')
    x1, y1 = src['x'], src['y']
    x2, y2 = tgt['x'], tgt['y']
    line = dwg.line(start=(x1, y1), end=(x2, y2), stroke=style['colors'].get('muted', '#999'),
                    stroke_width=style['line'].get('width', 1.2))
    g.add(line)
    g.add(dwg.desc(json.dumps({'id': eid, 'source': src.get('id'), 'target': tgt.get('id')})))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--style", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = load_json(args.data)
    style = load_json(args.style)
    canvas_w = style['canvas'].get('width_px', 1200)
    canvas_h = style['canvas'].get('height_px', 800)
    dwg = svgwrite.Drawing(args.out, size=(canvas_w, canvas_h))

    nodes = {n['id']: n for n in data.get('nodes', [])}
    # Draw edges first so nodes are on top
    for i, e in enumerate(data.get('edges', []), start=1):
        eid = e.get('id', f"e{i}")
        src = nodes[e['source']]
        tgt = nodes[e['target']]
        dwg.add(edge_group(dwg, eid, src, tgt, style))

    for n in data.get('nodes', []):
        dwg.add(node_group(dwg, n, style))

    # Add a simple title metadata
    dwg.set_desc(json.dumps({'title': data.get('meta', {}).get('title', ''), 'source': args.data}))
    dwg.save()
    print("Wrote", args.out)


if __name__ == '__main__':
    main()
