#!/usr/bin/env python3
"""
Tiny generator that reads nodes/edges JSON and a style JSON and emits an editable SVG.
Each node is a <g id="node-<id>"> and each edge is a <g id="edge-<id>">. Metadata is stored in <desc>.
This version supports richer node/edge schema: node shapes, overrides, arrow markers, dashed edges, layers.
"""
import json
import argparse
from pathlib import Path
import svgwrite


def load_json(p):
    return json.loads(Path(p).read_text())


def make_marker_defs(dwg, style):
    defs = dwg.defs
    # create a simple arrow marker for edges that need arrowheads
    marker_size = style.get('line', {}).get('marker_size', 6)
    stroke_color = style['colors'].get('primary', '#1b7a4a')
    marker = dwg.marker(insert=(marker_size/2, marker_size/2), size=(marker_size, marker_size), orient="auto")
    # triangle path pointing right; coordinate system of marker is markerUnits='strokeWidth' by default in svgwrite
    path_d = f"M0,0 L0,{marker_size} L{marker_size},{marker_size/2} z"
    marker.add(dwg.path(d=path_d, fill=stroke_color))
    marker['id'] = 'marker-arrow'
    defs.add(marker)
    return defs


def node_group(dwg, node, style):
    nid = node['id']
    label = node.get('label', nid)
    # style tokens and possible overrides
    w = node.get('width', style['node'].get('default_width', 120))
    h = node.get('height', style['node'].get('default_height', 36))
    rx = style['node'].get('rx', 4)
    fill = style['node'].get('fill', style['colors'].get('background', '#fff'))
    stroke = style['node'].get('stroke', style['colors'].get('primary', '#000'))
    stroke_w = style['node'].get('stroke_width', 1)
    font_size = style.get('fonts', {}).get('label', {}).get('size', 12)

    g = dwg.g(id=f"node-{nid}", class_="node", transform=f"translate({node['x']},{node['y']})")
    shape = node.get('shape', 'rect')
    if shape == 'rect':
        rect = dwg.rect(insert=(-w/2, -h/2), size=(w, h), rx=rx, fill=fill, stroke=stroke, stroke_width=stroke_w)
        g.add(rect)
    elif shape == 'circle':
        # use width as diameter if provided, else use height
        d = node.get('width', node.get('height', style['node'].get('default_width', 36)))
        r = d/2
        circle = dwg.circle(center=(0,0), r=r, fill=fill, stroke=stroke, stroke_width=stroke_w)
        g.add(circle)
    elif shape == 'ellipse':
        rx_ = w/2
        ry_ = h/2
        ell = dwg.ellipse(center=(0,0), r=(rx_, ry_), fill=fill, stroke=stroke, stroke_width=stroke_w)
        g.add(ell)
    # label
    text = dwg.text(label, insert=(-w/2 + 10, font_size/2 + 2), fill=style['colors'].get('text', '#111'), font_size=font_size)
    g.add(text)
    # embed metadata as JSON in desc
    meta = node.get('metadata', {})
    meta_combined = {'id': nid, 'label': label, 'role': node.get('role'), 'metadata': meta}
    g.add(dwg.desc(json.dumps(meta_combined)))
    return g


def edge_element(dwg, edge, src, tgt, style):
    # build a polyline (or line) between points; honor waypoints if provided
    points = []
    points.append((src['x'], src['y']))
    for wp in edge.get('waypoints', []) or []:
        points.append((wp[0], wp[1]))
    points.append((tgt['x'], tgt['y']))
    stroke_color = style['colors'].get('muted', '#999')
    line_w = style.get('line', {}).get('width', 1.2)
    stroke_style = edge.get('stroke_style', 'solid')
    if len(points) == 2:
        line = dwg.line(start=points[0], end=points[1], stroke=stroke_color, stroke_width=line_w)
    else:
        line = dwg.polyline(points=points, fill='none', stroke=stroke_color, stroke_width=line_w)
    if stroke_style == 'dashed':
        # simple dash pattern
        line.stroke_dasharray([6,4])
    # marker end
    if edge.get('marker_end') == 'arrow':
        # reference the marker defined in defs
        line.update({'marker-end': 'url(#marker-arrow)'})
    return line


def edge_group(dwg, eid, edge, src, tgt, style):
    g = dwg.g(id=f"edge-{eid}", class_='edge')
    line = edge_element(dwg, edge, src, tgt, style)
    g.add(line)
    # label
    if 'label' in edge and edge['label']:
        x1, y1 = src['x'], src['y']
        x2, y2 = tgt['x'], tgt['y']
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        px, py = -dy, dx
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
    # embed metadata
    meta = edge.get('metadata', {})
    meta_combined = {'id': eid, 'source': edge.get('source'), 'target': edge.get('target'), 'label': edge.get('label'), 'metadata': meta}
    g.add(dwg.desc(json.dumps(meta_combined)))
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

    # defs (markers, gradients)
    make_marker_defs(dwg, style)

    # named layers
    layer_bg = dwg.g(id='layer-background', **{"data-layer": "background"})
    layer_edges = dwg.g(id='layer-edges', **{"data-layer": "edges"})
    layer_nodes = dwg.g(id='layer-nodes', **{"data-layer": "nodes"})
    layer_ann = dwg.g(id='layer-annotations', **{"data-layer": "annotations"})

    # background rect in background layer
    layer_bg.add(dwg.rect(insert=(0,0), size=(canvas_w, canvas_h), fill=bg_color))

    nodes = {n['id']: n for n in data.get('nodes', [])}

    # edges
    for i, e in enumerate(data.get('edges', []), start=1):
        eid = e.get('id', f"e{i}")
        src = nodes.get(e['source'])
        tgt = nodes.get(e['target'])
        if not src or not tgt:
            # skip invalid edge
            continue
        eg = edge_group(dwg, eid, e, src, tgt, style)
        layer_edges.add(eg)

    # nodes
    for n in data.get('nodes', []):
        ng = node_group(dwg, n, style)
        # annotations layer: nodes with role 'annotation'
        if n.get('role') == 'annotation':
            layer_ann.add(ng)
        else:
            layer_nodes.add(ng)

    # assemble layers in order
    dwg.add(layer_bg)
    dwg.add(layer_edges)
    dwg.add(layer_nodes)
    dwg.add(layer_ann)

    # Add a simple title metadata
    dwg.set_desc(json.dumps({'title': data.get('meta', {}).get('title', ''), 'source': args.data}))
    dwg.save()
    print("Wrote", args.out)


if __name__ == '__main__':
    main()
