#!/usr/bin/env python3
"""
Minimal figure generator that consumes a small data-driven figure spec (JSON), a style profile, and emits an SVG.
Supported: simple linear scales, axes (bottom/left), and marks: line, point, bar. Intended as a lightweight layer on top of pipeline_b.
This version also writes a companion .meta.json manifest with provenance info (spec path, style path, generator version, timestamp, artifact sha256/size).
"""
import json
import argparse
from pathlib import Path
import svgwrite
import math
import hashlib
import datetime
import os

__version__ = "0.1"

def load_json(p):
    return json.loads(Path(p).read_text())

def compute_scale(domain, range_):
    d0, d1 = domain
    r0, r1 = range_
    def scale(v):
        if d1 == d0:
            return (r0 + r1) / 2
        return r0 + (v - d0) * (r1 - r0) / (d1 - d0)
    return scale

def draw_axes(dwg, layer_axes, scales, style, plot_area, margins):
    # plot_area: (left, top, width, height)
    left, top, width, height = plot_area
    x0, y0 = left, top
    x1, y1 = left + width, top + height
    axis_color = style['colors'].get('axis', '#333333')
    tick_color = style['colors'].get('muted', '#9aa6a6')
    font_size = style.get('fonts', {}).get('label', {}).get('size', 10)
    # x axis (bottom)
    if 'xscale' in scales:
        # baseline at y1
        layer_axes.add(dwg.line(start=(x0, y1), end=(x1, y1), stroke=axis_color, stroke_width=1))
        # ticks
        ticks = 5
        domain = scales['xscale']['domain']
        for i in range(ticks+1):
            tval = domain[0] + (domain[1]-domain[0]) * i / ticks
            sx = scales['xscale']['scale'](tval)
            layer_axes.add(dwg.line(start=(sx, y1), end=(sx, y1+6), stroke=tick_color))
            layer_axes.add(dwg.text(str(round(tval,2)), insert=(sx-6, y1+20), font_size=font_size, fill=axis_color))
    # y axis (left)
    if 'yscale' in scales:
        layer_axes.add(dwg.line(start=(x0, y0), end=(x0, y1), stroke=axis_color, stroke_width=1))
        ticks = 5
        domain = scales['yscale']['domain']
        for i in range(ticks+1):
            tval = domain[0] + (domain[1]-domain[0]) * i / ticks
            sy = scales['yscale']['scale'](tval)
            # sy is pixel y (smaller at top) - draw tick
            layer_axes.add(dwg.line(start=(x0-6, sy), end=(x0, sy), stroke=tick_color))
            layer_axes.add(dwg.text(str(round(tval,2)), insert=(x0-40, sy+4), font_size=font_size, fill=axis_color))

def generate_figure(spec, style, out_path):
    canvas_w = style['canvas'].get('width_px', 1200)
    canvas_h = style['canvas'].get('height_px', 800)
    margin = style.get('canvas', {}).get('margin_px', 48)
    bg_color = style['colors'].get('background', '#ffffff')

    dwg = svgwrite.Drawing(out_path, size=(canvas_w, canvas_h))
    # layers
    layer_bg = dwg.g(id='layer-background')
    layer_axes = dwg.g(id='layer-axes')
    layer_marks = dwg.g(id='layer-marks')
    layer_ann = dwg.g(id='layer-annotations')

    layer_bg.add(dwg.rect(insert=(0,0), size=(canvas_w, canvas_h), fill=bg_color))

    # define plot area (simple single panel)
    left = margin
    right = canvas_w - margin
    top = margin
    bottom = canvas_h - margin
    plot_w = right - left
    plot_h = bottom - top

    # prepare scales
    scales = {}
    for sname, sdef in spec.get('scales', {}).items():
        stype = sdef.get('type', 'linear')
        if stype == 'linear':
            domain = sdef.get('domain')
            if domain is None:
                # infer later
                domain = [0,1]
            # range for x: left->right, for y: bottom->top (inverted)
            if sname.lower().startswith('x'):
                range_ = [left, right]
            else:
                range_ = [bottom, top]
            scales[sname] = {'domain': domain, 'range': range_, 'scale': compute_scale(domain, range_)}
        else:
            # ordinal not implemented fully; placeholder
            scales[sname] = {'domain': sdef.get('domain', []), 'range': sdef.get('range', [])}

    # If domains are missing, try to infer from data for x/y scales
    data_map = {d['name']: d['values'] for d in spec.get('data', [])}
    for mark in spec.get('marks', []):
        enc = mark.get('encoding', {})
        for axis in ('x','y'):
            if axis in enc:
                scname = enc[axis]['scale']
                field = enc[axis]['field']
                s = scales.get(scname)
                if s and (s['domain'] == [0,1] or s['domain'] is None):
                    vals = [v.get(field) for v in data_map.get(mark['from'], []) if v.get(field) is not None]
                    if vals:
                        mn = min(vals)
                        mx = max(vals)
                        # expand a bit
                        if mn == mx:
                            mn -= 0.5
                            mx += 0.5
                        s['domain'] = [mn, mx]
                        s['scale'] = compute_scale(s['domain'], s['range'])

    # draw axes
    plot_area = (left, top, plot_w, plot_h)
    draw_axes(dwg, layer_axes, scales, style, plot_area, margin)

    # render marks
    for mark in spec.get('marks', []):
        mtype = mark['type']
        dataset = data_map.get(mark['from'], [])
        enc = mark.get('encoding', {})
        color_val = enc.get('color', {}).get('value', style['colors'].get('primary'))
        size_val = enc.get('size', {}).get('value', 6)
        # compute pixel coords
        pts = []
        for row in dataset:
            x = row.get(enc['x']['field'])
            y = row.get(enc['y']['field'])
            if x is None or y is None:
                continue
            sx = scales[enc['x']['scale']]['scale'](x)
            sy = scales[enc['y']['scale']]['scale'](y)
            pts.append((sx, sy))
        if mtype == 'line' and pts:
            layer_marks.add(dwg.polyline(points=pts, fill='none', stroke=color_val, stroke_width=style.get('line', {}).get('width', 1.5)))
        if mtype == 'point' and pts:
            for (sx, sy) in pts:
                layer_marks.add(dwg.circle(center=(sx, sy), r=size_val, fill=color_val, stroke='none'))
        if mtype == 'bar' and pts:
            # treat x as discrete positions; simple bar width from style tokens
            bar_w = style.get('plot_tokens', {}).get('bar_width', 0.8)
            # compute pixel width: approximate spacing between x ticks
            if len(pts) > 1:
                pixel_w = abs(pts[1][0] - pts[0][0]) * bar_w
            else:
                pixel_w = 10
            for (sx, sy), row in zip(pts, dataset):
                # baseline at y corresponding to 0
                base = scales['yscale']['scale'](0) if 'yscale' in scales else bottom
                x_left = sx - pixel_w/2
                h = abs(base - sy)
                y_top = min(base, sy)
                layer_marks.add(dwg.rect(insert=(x_left, y_top), size=(pixel_w, h), fill=color_val))

    # assemble
    dwg.add(layer_bg)
    dwg.add(layer_axes)
    dwg.add(layer_marks)
    dwg.add(layer_ann)

    # metadata
    dwg.set_desc(json.dumps({'title': spec.get('meta', {}).get('title', ''), 'source': 'figure_spec'}))
    dwg.save()


def write_manifest(out_path, spec_path, style_path, style):
    # compute file size and sha256
    p = Path(out_path)
    try:
        size = p.stat().st_size
    except Exception:
        size = None
    sha256 = None
    try:
        with open(out_path, 'rb') as f:
            data = f.read()
            sha256 = hashlib.sha256(data).hexdigest()
    except Exception:
        sha256 = None
    manifest = {
        'spec_path': str(spec_path),
        'style_path': str(style_path),
        'style_name': style.get('name'),
        'style_version': style.get('version'),
        'generator': {'name': 'generate_figure_svg.py', 'version': __version__},
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'artifact': {
            'path': str(out_path),
            'size_bytes': size,
            'sha256': sha256
        }
    }
    manifest_path = str(out_path) + '.meta.json'
    Path(manifest_path).write_text(json.dumps(manifest, indent=2))
    print('Wrote manifest', manifest_path)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--style', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    spec = load_json(args.spec)
    style = load_json(args.style)
    generate_figure(spec, style, args.out)
    # write companion manifest for provenance
    write_manifest(args.out, args.spec, args.style, style)
