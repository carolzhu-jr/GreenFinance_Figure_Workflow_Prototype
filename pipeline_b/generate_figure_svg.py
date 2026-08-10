#!/usr/bin/env python3
"""
Minimal figure generator that consumes a small data-driven figure spec (JSON), a style profile, and emits an SVG.
Supports: simple linear scales, axes (bottom/left), marks: line, point, bar, lightweight legends, panels (multi-panel layout), and a provenance manifest.
"""
import json
import argparse
from pathlib import Path
import svgwrite
import math
import hashlib
import datetime
import subprocess

__version__ = "0.3"


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


def draw_axes(dwg, layer_axes, scales, style, plot_area, font_size):
    # plot_area: (left, top, width, height)
    left, top, width, height = plot_area
    x0, y0 = left, top
    x1, y1 = left + width, top + height
    axis_color = style['colors'].get('axis', '#333333')
    tick_color = style['colors'].get('muted', '#9aa6a6')
    # x axis (bottom)
    if 'xscale' in scales:
        layer_axes.add(dwg.line(start=(x0, y1), end=(x1, y1), stroke=axis_color, stroke_width=1))
        ticks = 5
        domain = scales['xscale']['domain']
        for i in range(ticks+1):
            tval = domain[0] + (domain[1]-domain[0]) * i / ticks
            sx = scales['xscale']['scale'](tval)
            layer_axes.add(dwg.line(start=(sx, y1), end=(sx, y1+6), stroke=tick_color))
            layer_axes.add(dwg.text(str(round(tval,2)), insert=(sx-6, y1+20), font_size=font_size, fill=axis_color))
    if 'yscale' in scales:
        layer_axes.add(dwg.line(start=(x0, y0), end=(x0, y1), stroke=axis_color, stroke_width=1))
        ticks = 5
        domain = scales['yscale']['domain']
        for i in range(ticks+1):
            tval = domain[0] + (domain[1]-domain[0]) * i / ticks
            sy = scales['yscale']['scale'](tval)
            layer_axes.add(dwg.line(start=(x0-6, sy), end=(x0, sy), stroke=tick_color))
            layer_axes.add(dwg.text(str(round(tval,2)), insert=(x0-40, sy+4), font_size=font_size, fill=axis_color))


def get_git_commit_sha():
    try:
        out = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL)
        return out.decode('utf-8').strip()
    except Exception:
        return None


def write_manifest(out_path, spec_path, style_path, style):
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
    commit_sha = get_git_commit_sha()
    manifest = {
        'spec_path': str(spec_path),
        'style_path': str(style_path),
        'style_name': style.get('name'),
        'style_version': style.get('version'),
        'generator': {'name': 'generate_figure_svg.py', 'version': __version__},
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'commit_sha': commit_sha,
        'artifact': {
            'path': str(out_path),
            'size_bytes': size,
            'sha256': sha256
        }
    }
    manifest_path = str(out_path) + '.meta.json'
    Path(manifest_path).write_text(json.dumps(manifest, indent=2))
    print('Wrote manifest', manifest_path)


def render_marks_in_area(dwg, layer_marks, marks, data_map, scales, style, panel_bounds):
    # panel_bounds: left, top, width, height
    left, top, width, height = panel_bounds
    # reuse previous mark rendering logic but confined to computed scales
    for mark in marks:
        mtype = mark['type']
        dataset = data_map.get(mark['from'], [])
        enc = mark.get('encoding', {})
        color_enc = enc.get('color', {})
        size_val = enc.get('size', {}).get('value', 6)
        def color_for_row(row):
            if 'value' in color_enc:
                return color_enc['value']
            if 'field' in color_enc:
                v = row.get(color_enc['field'])
                # fallback to primary
                return style['colors'].get('primary')
            return style['colors'].get('primary')
        pts = []
        for row in dataset:
            x = row.get(enc['x']['field'])
            y = row.get(enc['y']['field'])
            if x is None or y is None:
                continue
            sx = scales[enc['x']['scale']]['scale'](x)
            sy = scales[enc['y']['scale']]['scale'](y)
            pts.append((sx, sy, row))
        if mtype == 'line' and pts:
            pts_xy = [(p[0], p[1]) for p in pts]
            layer_marks.add(dwg.polyline(points=pts_xy, fill='none', stroke=color_for_row(pts[0][2]), stroke_width=style.get('line', {}).get('width', 1.5)))
        if mtype == 'point' and pts:
            for (sx, sy, row) in pts:
                c = color_for_row(row)
                layer_marks.add(dwg.circle(center=(sx, sy), r=size_val, fill=c, stroke='none'))
        if mtype == 'bar' and pts:
            bar_w = style.get('plot_tokens', {}).get('bar_width', 0.8)
            if len(pts) > 1:
                pixel_w = abs(pts[1][0] - pts[0][0]) * bar_w
            else:
                pixel_w = 10
            for (sx, sy, row) in pts:
                base = scales['yscale']['scale'](0) if 'yscale' in scales else (top + height)
                x_left = sx - pixel_w/2
                h = abs(base - sy)
                y_top = min(base, sy)
                layer_marks.add(dwg.rect(insert=(x_left, y_top), size=(pixel_w, h), fill=color_for_row(row)))


def generate_figure(spec, style, out_path):
    canvas_w = style['canvas'].get('width_px', 1200)
    canvas_h = style['canvas'].get('height_px', 800)
    margin = style.get('canvas', {}).get('margin_px', 48)
    bg_color = style['colors'].get('background', '#ffffff')

    dwg = svgwrite.Drawing(out_path, size=(canvas_w, canvas_h))
    layer_bg = dwg.g(id='layer-background')
    layer_axes = dwg.g(id='layer-axes')
    layer_marks = dwg.g(id='layer-marks')
    layer_ann = dwg.g(id='layer-annotations')
    layer_legend = dwg.g(id='layer-legend')

    layer_bg.add(dwg.rect(insert=(0,0), size=(canvas_w, canvas_h), fill=bg_color))

    left = margin
    right = canvas_w - margin
    top = margin
    bottom = canvas_h - margin
    plot_w = right - left
    plot_h = bottom - top

    # top-level scales available as templates (domain may be inferred per panel)
    base_scales = {}
    for sname, sdef in spec.get('scales', {}).items():
        stype = sdef.get('type', 'linear')
        if stype == 'linear':
            domain = sdef.get('domain')
            if domain is None:
                domain = [0,1]
            base_scales[sname] = {'domain': domain, 'type': 'linear'}
        else:
            base_scales[sname] = {'domain': sdef.get('domain', []), 'type': stype}

    data_map = {d['name']: d['values'] for d in spec.get('data', [])}

    # panel handling
    panels_spec = spec.get('panels')
    if panels_spec:
        rows = panels_spec.get('layout', {}).get('rows', 1)
        cols = panels_spec.get('layout', {}).get('cols', 1)
        panels = panels_spec.get('panels', [])
        panel_w = plot_w / cols
        panel_h = plot_h / rows
        # iterate panel grid
        for p in panels:
            prow = p.get('row', 0)
            pcol = p.get('col', 0)
            panel_left = left + pcol * panel_w
            panel_top = top + prow * panel_h
            panel_bounds = (panel_left, panel_top, panel_w, panel_h)
            # setup scales for panel
            scales = {}
            # copy base scales
            for name, info in base_scales.items():
                if info['type'] == 'linear':
                    if name.lower().startswith('x'):
                        range_ = [panel_left, panel_left + panel_w]
                    else:
                        range_ = [panel_top + panel_h, panel_top]
                    scales[name] = {'domain': info['domain'], 'range': range_, 'scale': compute_scale(info['domain'], range_)}
                else:
                    scales[name] = {'domain': info['domain'], 'range': info.get('range', [])}
            # marks for this panel: prefer p['marks'], else top-level marks
            panel_marks = p.get('marks', spec.get('marks', []))
            # infer missing domains from panel data
            for mark in panel_marks:
                enc = mark.get('encoding', {})
                for axis in ('x', 'y'):
                    if axis in enc:
                        scname = enc[axis]['scale']
                        field = enc[axis]['field']
                        s = scales.get(scname)
                        if s and (s['domain'] == [0,1] or s['domain'] is None):
                            vals = [v.get(field) for v in data_map.get(mark['from'], []) if v.get(field) is not None]
                            if vals:
                                mn = min(vals)
                                mx = max(vals)
                                if mn == mx:
                                    mn -= 0.5
                                    mx += 0.5
                                s['domain'] = [mn, mx]
                                s['scale'] = compute_scale(s['domain'], s['range'])
            # draw axes for this panel
            font_size = style.get('fonts', {}).get('label', {}).get('size', 10)
            draw_axes(dwg, layer_axes, scales, style, panel_bounds, font_size)
            # render marks in this panel
            render_marks_in_area(dwg, layer_marks, panel_marks, data_map, scales, style, panel_bounds)
            # add optional panel title
            if 'title' in p:
                tt = dwg.text(p['title'], insert=(panel_left + 6, panel_top + 14), font_size=style.get('fonts', {}).get('title', {}).get('size', 12), fill=style['colors'].get('text', '#111'))
                layer_ann.add(tt)
    else:
        # single-panel behavior (existing)
        scales = {}
        for sname, sdef in spec.get('scales', {}).items():
            stype = sdef.get('type', 'linear')
            if stype == 'linear':
                domain = sdef.get('domain')
                if domain is None:
                    domain = [0,1]
                if sname.lower().startswith('x'):
                    range_ = [left, right]
                else:
                    range_ = [bottom, top]
                scales[sname] = {'domain': domain, 'range': range_, 'scale': compute_scale(domain, range_)}
            else:
                scales[sname] = {'domain': sdef.get('domain', []), 'range': sdef.get('range', [])}
        # infer domains
        for mark in spec.get('marks', []):
            enc = mark.get('encoding', {})
            for axis in ('x', 'y'):
                if axis in enc:
                    scname = enc[axis]['scale']
                    field = enc[axis]['field']
                    s = scales.get(scname)
                    if s and (s['domain'] == [0,1] or s['domain'] is None):
                        vals = [v.get(field) for v in data_map.get(mark['from'], []) if v.get(field) is not None]
                        if vals:
                            mn = min(vals)
                            mx = max(vals)
                            if mn == mx:
                                mn -= 0.5
                                mx += 0.5
                            s['domain'] = [mn, mx]
                            s['scale'] = compute_scale(s['domain'], s['range'])
        # draw axes and marks for single panel
        plot_area = (left, top, plot_w, plot_h)
        font_size = style.get('fonts', {}).get('label', {}).get('size', 10)
        draw_axes(dwg, layer_axes, scales, style, plot_area, font_size)
        render_marks_in_area(dwg, layer_marks, spec.get('marks', []), data_map, scales, style, plot_area)

    # legend (global): same simple behavior as before
    legend_entries = []
    for mark in spec.get('marks', []) if not spec.get('panels') else [m for p in spec.get('panels', {}).get('panels', []) for m in p.get('marks', [])]:
        enc = mark.get('encoding', {})
        color_enc = enc.get('color', {})
        if 'field' in color_enc:
            field = color_enc['field']
            values = [row.get(field) for row in data_map.get(mark['from'], []) if row.get(field) is not None]
            cats = []
            for v in values:
                if v not in cats:
                    cats.append(v)
            cmap_name = color_enc.get('map') or 'qualitative'
            colormap = style.get('colormaps', {}).get(cmap_name, style.get('colormaps', {}).get('qualitative', ['#1b7a4a', '#ffd166']))
            for i, cat in enumerate(cats):
                color = colormap[i % len(colormap)]
                legend_entries.append((str(cat), color))
            break
    if legend_entries:
        legend_x = right - 160
        legend_y = top + 10
        spacing = 18
        sw = 12
        font_size = style.get('fonts', {}).get('label', {}).get('size', 12)
        lg = dwg.g(id='legend', class_='legend')
        for i, (label, color) in enumerate(legend_entries):
            y = legend_y + i * spacing
            rect = dwg.rect(insert=(legend_x, y), size=(sw, sw), fill=color, stroke='none')
            text = dwg.text(label, insert=(legend_x + sw + 6, y + sw - 2), font_size=font_size, fill=style['colors'].get('text', '#111'))
            lg.add(rect)
            lg.add(text)
        layer_legend.add(lg)

    # assemble layers
    dwg.add(layer_bg)
    dwg.add(layer_axes)
    dwg.add(layer_marks)
    dwg.add(layer_legend)
    dwg.add(layer_ann)

    dwg.set_desc(json.dumps({'title': spec.get('meta', {}).get('title', ''), 'source': 'figure_spec'}))
    dwg.save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--style', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    spec = load_json(args.spec)
    style = load_json(args.style)
    generate_figure(spec, style, args.out)
    write_manifest(args.out, args.spec, args.style, style)

if __name__ == '__main__':
    main()
