#!/usr/bin/env python3
"""
Tiny generator that reads nodes/edges JSON and a style JSON and emits an editable SVG.
Each node is a <g id="node-<id>"> and each edge is a <g id="edge-<id>">. Metadata is stored in <desc>.
This version fully consumes the expanded style profile in profiles/default_style.json.
"""
import json
import argparse
from pathlib import Path
import svgwrite


def load_json(p):
    return json.loads(Path(p).read_text())


def node_group(dwg, node, style):
    nid = node['id']
    label = node.get('label', nid)
    # style tokens
    w = style['node'].get('default_width', 120)
    h = style['node'].get('default_height', 36)
    rx = style['node'].get('rx', 4)
    fill = style['node'].get('fill', style['colors'].get('background', '#fff'))
    stroke = style['node'].get('stroke', style['colors'].get('primary', '#000'))
    stroke_w = style['node'].get('stroke_width', 1)
    font_size = style.get('fonts', {}).get('label', {}).get('size', 12)

    g = dwg.g(id=f"node-{nid}", class_="node", transform=f"translate({node['x']},{node['y']})")
    rect = dwg.rect(insert=(-w/2, -h/2), size=(w, h), rx=rx, fill=fill, stroke=stroke, stroke_width=stroke_w)
    g.add(rect)
    # text baseline: approximate y offset
    text = dwg.text(label, insert=(-w/2 + 10, font_size/2 + 2), fill=style['colors'].get('text', '#111'), font_size=font_size)
    g.add(text)
    # Embed metadata in a desc element for round-tripping
    g.add(dwg.desc(json.dumps({'id': nid, 'label': label})))
    return g


def edge_group(dwg, eid, src, tgt, style):
    g = dwg.g(id=f"edge-{eid}", class_='edge')
    x1, y1 = src['x'], src['y']
    x2, y2 = tgt['x'], tgt['y']
    stroke_color = style['colors'].get('muted', '#999')
    line_w = style.get('line', {}).get('width', 1.2)
    line = dwg.line(start=(x1, y1), end=(x2, y2), stroke=stroke_color, stroke_width=line_w)
    g.add(line)
    # optional edge label
    label = ''
    if 'label' in src and 'label' in tgt:
        # if both have labels, prefer edge's own label
        label = ''
    # use edge's label if provided on edge metadata; otherwise skip
    # place label at midpoint slightly offset
    # use annotation font if present
    annotation_font = style.get('fonts', {}).get('annotation', {})
    ann_size = annotation_font.get('size', None) if isinstance(annotation_font, dict) else None
    if ann_size is None:
        ann_size = style.get('fonts', {}).get('label', {}).get('size', 10)

    # If the edge dictionary included a 'label' this function expects the caller
    # to pass it (we will read it before calling this helper). The g element
    # still contains a desc with metadata so editors can round-trip.
    return g


def edge_group_with_label(dwg, eid, src, tgt, edge, style):
    # Build base edge group
    g = edge_group(dwg, eid, src, tgt, style)
    # add label if present
    if 'label' in edge and edge['label']:
        x1, y1 = src['x'], src['y']
        x2, y2 = tgt['x'], tgt['y']
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # offset perpendicular vector for readability
        dx, dy = x2 - x1, y2 - y1
        # perpendicular
        px, py = -dy, dx
        # normalize and scale
        import math
        norm = math.hypot(px, py)
        if norm == 0:
            ox, oy = 0, -10
        else:
            ox, oy = (px / norm * 10, py / norm * 10)
        ann_font = style.get('fonts', {}).get('annotation', {})
        ann_size = ann_font.get('size', style.get('fonts', {}).get('label', {}).get('size', 10))
        text = dwg.text(edge['label'], insert=(mx + ox, my + oy + ann_size/2), fill=style['colors'].get('text', '#111'), font_size=ann_size)
        g.add(text)
    # attach edge metadata in desc
    g.add(dwg.desc(json.dumps({'id': eid, 'source': src.get('id'), 'target': tgt.get('id'), 'label': edge.get('label')})))
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
    bg_color = style['colors'].get('background', '#ffffff')

    dwg = svgwrite.Drawing(args.out, size=(canvas_w, canvas_h))

    # add background rect so opening in editors shows the intended background color
    dwg.add(dwg.rect(insert=(0, 0), size=(canvas_w, canvas_h), fill=bg_color))

    nodes = {n['id']: n for n in data.get('nodes', [])}
    # Draw edges first so nodes are on top
    for i, e in enumerate(data.get('edges', []), start=1):
        eid = e.get('id', f"e{i}")
        src = nodes[e['source']]
        tgt = nodes[e['target']]
        dwg.add(edge_group_with_label(dwg, eid, src, tgt, e, style))

    for n in data.get('nodes', []):
        dwg.add(node_group(dwg, n, style))

    # Add a simple title metadata
    dwg.set_desc(json.dumps({'title': data.get('meta', {}).get('title', ''), 'source': args.data}))
    dwg.save()
    print("Wrote", args.out)


if __name__ == '__main__':
    main()
