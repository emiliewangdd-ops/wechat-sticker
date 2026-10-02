"""Build a configured sticker; publish only after decoded-GIF checks pass.

Usage: python3 scripts/build_dynamic_sticker.py path/to/config.json
Paths in config are relative to config.json. Requires Pillow and NumPy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glyph_height(image):
    a = np.array(image.convert('RGBA'))
    mask = (a[:, :, 3] >= 128) & (a[:, :, :3].max(axis=2) < 40)
    ys = np.where(mask)[0]
    require(len(ys) > 0, 'Text has no visible black glyph')
    return int(ys.max() - ys.min() + 1)


def check_glyph_height(image, expected, maximum=None):
    actual = glyph_height(image)
    if maximum is not None:
        require(actual <= maximum + 10, 'Black glyph height exceeds approved reference maximum plus bounded tolerance')
    # Generated brush masters can lose a few edge pixels during the locked
    # downscale; keep a bounded tolerance while preserving the same visual size.
    require(abs(actual - expected) <= 10, 'Final black glyph height differs from expected height')
    return actual


def action_component_sizes(mask):
    """Return 8-connected visible-component sizes for an alpha mask."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    sizes = []
    for y, x in zip(*np.where(mask)):
        if seen[y, x]:
            continue
        stack = [(int(y), int(x))]
        seen[y, x] = True
        count = 0
        while stack:
            yy, xx = stack.pop()
            count += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = yy + dy, xx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        sizes.append(count)
    return sizes


def has_small_edge_component(mask, max_size, edge_pixels=16):
    """Detect any disconnected component suspiciously close to a source edge."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    components = []
    for y, x in zip(*np.where(mask)):
        if seen[y, x]:
            continue
        stack = [(int(y), int(x))]
        seen[y, x] = True
        points = []
        while stack:
            yy, xx = stack.pop()
            points.append((yy, xx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = yy + dy, xx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        ys = [p[0] for p in points]
        xs = [p[1] for p in points]
        components.append((len(points), min(xs), min(ys), max(xs), max(ys)))
    largest = max((c[0] for c in components), default=0)
    for size, min_x, min_y, max_x, max_y in components:
        near_edge = min_x < edge_pixels or max_x >= w - edge_pixels or min_y < edge_pixels or max_y >= h - edge_pixels
        if near_edge and size < largest and (not max_size or size <= max_size or size < largest):
            return True
    return False


def build(config_path):
    config_path = Path(config_path).resolve()
    raw = json.loads(config_path.read_text())
    root = config_path.parent
    resolve = lambda p: (root / p).resolve()
    if 'baseline' in raw:
        allowed = {'baseline', 'name', 'text_id', 'frames', 'checks', 'output'}
        require(set(raw).issubset(allowed), 'Single-sticker config attempts to override locked baseline')
        baseline_path = resolve(raw['baseline'])
        baseline = json.loads(baseline_path.read_text())
        require(raw['text_id'] in baseline['text_masters'], 'Unknown or unapproved text master')
        reference = baseline['fixed'].get('reference_text_metrics', {})
        if reference:
            reference_path = (baseline_path.parent / reference['source']).resolve()
            require(digest(reference_path) == reference['sha256'], 'Reference GIF hash mismatch')
            with Image.open(reference_path) as ref:
                for frame_index in range(ref.n_frames):
                    ref.seek(frame_index)
                    measured = glyph_height(ref.convert('RGBA').crop(reference['measurement_roi']))
                    require(measured == reference['black_height'], 'Reference glyph height mismatch')
            require(reference['maximum_black_height'] == reference['black_height'], 'Reference maximum must equal reference height')
        c = dict(baseline['fixed'])
        c.update({key: raw[key] for key in ('frames', 'checks', 'output')})
        c['text'] = dict(baseline['text_masters'][raw['text_id']])
        c['text']['path'] = str((baseline_path.parent / c['text']['path']).resolve())
        c['name'] = raw['name']
        baseline_hash = digest(baseline_path)
    else:
        c = raw
        baseline_hash = None
    checks = resolve(c['checks'])
    checks.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'config_sha256': digest(config_path), 'baseline_sha256': baseline_hash,
              'script_sha256': digest(Path(__file__)), 'sources': []}
    try:
        size = tuple(c.get('canvas', [512, 512]))
        box = c['action_box']
        left, top, right, bottom = box
        require(0 <= left < right <= size[0] and 0 <= top < bottom <= size[1], 'Invalid action box')
        threshold = c.get('alpha_threshold', 128)
        require(1 <= threshold <= 255, 'Invalid alpha threshold')
        durations = c['durations']
        require(len(durations) == len(c['frames']) and len(durations) > 1, 'Frame/duration mismatch')
        require(all(isinstance(d, int) and d > 0 and d % 10 == 0 for d in durations), 'Durations must be positive multiples of 10ms')
        text_spec = c['text']
        min_component_pixels = c.get('min_action_component_pixels', 0)
        max_edge_component_pixels = c.get('max_edge_component_pixels', 0)
        source_vertical_margin = c.get('source_vertical_margin', 0)
        require(isinstance(min_component_pixels, int) and min_component_pixels >= 0, 'Invalid minimum action component size')
        require(isinstance(max_edge_component_pixels, int) and max_edge_component_pixels >= 0, 'Invalid maximum edge component size')
        require(isinstance(source_vertical_margin, int) and source_vertical_margin >= 0, 'Invalid source vertical margin')
        text_path = resolve(text_spec['path'])
        require(digest(text_path) == text_spec['sha256'], 'Approved text master changed')
        text = Image.open(text_path).convert('RGBA')
        tb = text.getchannel('A').point(lambda v: 255 if v >= threshold else 0).getbbox()
        require(tb is not None, 'Empty text')
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        if 'text_box' not in c:
            require(text_spec['min_visible_width'] <= tw <= text_spec['max_visible_width'], 'Text visible width out of range')
            require(text_spec['min_visible_height'] <= th <= text_spec['max_visible_height'], 'Text visible height out of range')
        legacy_tx, legacy_ty = text_spec.get('position', [0, 0])
        text_box = c.get('text_box', [legacy_tx, legacy_ty, legacy_tx + text.width, legacy_ty + text.height])
        tx, ty, tx2, ty2 = text_box
        require(0 <= tx < tx2 <= size[0] and 0 <= ty < ty2 <= size[1], 'Invalid text box')
        text = text.crop(tb)
        metrics = c.get('reference_text_metrics', {})
        if metrics.get('sizing_policy') == 'height_first_then_uniform_width_fit':
            target = metrics['black_height']
            source_height = glyph_height(text)
            height_scale = target / source_height
            width_factor = min(1.0, (tx2-tx) / (text.width * height_scale))
            fit = height_scale * width_factor
            expected_height = target * width_factor
        else:
            fit = min((tx2-tx)/text.width, (ty2-ty)/text.height)
            expected_height = None
        text = text.resize((max(1, round(text.width*fit)), max(1, round(text.height*fit))), Image.Resampling.LANCZOS)
        require(text.height <= ty2-ty, 'Text including outline exceeds reserved height; do not silently shrink')
        if expected_height is not None:
            actual = check_glyph_height(text, expected_height, metrics['maximum_black_height'])
            report['text_metrics'] = {'target_black_height': target, 'expected_black_height': expected_height,
                                      'actual_black_height': actual, 'width_factor': width_factor,
                                      'width_limited': width_factor < 1, 'rendered_size': text.size}
        text_layer = Image.new('RGBA', size)
        text_layer.alpha_composite(text, (tx + (tx2-tx-text.width)//2, ty + (ty2-ty-text.height)//2))
        require(tx2 <= left or tx >= right or ty2 <= top or ty >= bottom, 'Text box overlaps reserved action box')
        parts = []
        for spec in c['frames']:
            path = resolve(spec['path'])
            source = Image.open(path).convert('RGBA')
            roi = spec.get('roi', [0, 0, *source.size])
            require(0 <= roi[0] < roi[2] <= source.width and 0 <= roi[1] < roi[3] <= source.height, 'ROI outside source')
            q = source.crop(roi)
            mask = np.array(q.getchannel('A')) >= threshold
            require(mask.any(), 'Empty action frame')
            require(not (mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any()), 'Extraction boundary crosses visible artwork')
            if source_vertical_margin:
                require(not mask[:source_vertical_margin].any() and not mask[-source_vertical_margin:].any(),
                        'Action source lacks required top/bottom clearance; regenerate with more margin')
            if min_component_pixels:
                require(min(action_component_sizes(mask)) >= min_component_pixels,
                        'Action source contains an isolated tiny component; remove stray pixels or regenerate')
            require(not has_small_edge_component(mask, max_edge_component_pixels),
                    'Action source contains a small component near an edge; remove stray pixels or regenerate')
            a = np.array(q)
            a[:,:,3] = np.where(mask, 255, 0)
            q = Image.fromarray(a)
            q = q.crop(q.getbbox())
            units = spec.get('source_units_scale', 1.0)
            require(units > 0, 'Invalid source coordinate conversion')
            if units != 1:
                require(bool(spec.get('scale_reason')), 'Separate-source scale requires documented reason')
                q = q.resize((max(1, round(q.width*units)), max(1, round(q.height*units))), Image.Resampling.LANCZOS)
            parts.append(q)
            report['sources'].append({'path': str(path), 'sha256': digest(path), 'roi': roi, 'content_size': q.size, 'source_units_scale': units})
        wmax = max(q.width for q in parts)
        hmax = max(q.height for q in parts)
        action_margin = c.get('action_safe_margin', 0)
        require(isinstance(action_margin, int) and action_margin >= 0, 'Invalid action safe margin')
        inner_left, inner_top = left + action_margin, top + action_margin
        inner_right, inner_bottom = right - action_margin, bottom - action_margin
        require(inner_left < inner_right and inner_top < inner_bottom, 'Action safe margin leaves no usable area')
        scale = min((inner_right-inner_left)/wmax, (inner_bottom-inner_top)/hmax)
        report.update(max_content_size=[wmax, hmax], scale=scale, frames=[])
        base = Image.new('RGBA', size)
        base.alpha_composite(text_layer)
        frames = []
        ax, ay = c.get('anchor', [0.5, 1.0])
        require(0 <= ax <= 1 and 0 <= ay <= 1, 'Invalid shared anchor')
        for i, q in enumerate(parts):
            q = q.resize((max(1, round(q.width*scale)), max(1, round(q.height*scale))), Image.Resampling.LANCZOS)
            x = inner_left + round((inner_right-inner_left-q.width)*ax)
            y = inner_top + round((inner_bottom-inner_top-q.height)*ay)
            require(x >= inner_left and y >= inner_top and x+q.width <= inner_right and y+q.height <= inner_bottom, 'Action clipped')
            f = base.copy()
            f.alpha_composite(q, (x,y))
            frames.append(f)
            f.save(checks / f'source-{i:02d}.png')
            report['frames'].append({'position':[x,y], 'size':q.size, 'duration':durations[i]})
        atlas = Image.new('RGB', (size[0], size[1]*len(frames)))
        for i,f in enumerate(frames):
            atlas.paste(f.convert('RGB'), (0, i*size[1]))
        palette = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        indexed = []
        for f in frames:
            p = f.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE)
            a = np.array(p)
            a[np.array(f.getchannel('A')) < threshold] = 255
            p = Image.fromarray(a).convert('P')
            p.putpalette(palette.getpalette())
            indexed.append(p)
        candidate = checks / 'candidate.gif'
        indexed[0].save(candidate, save_all=True, append_images=indexed[1:], duration=durations,
                        loop=0, transparency=255, disposal=2, optimize=False)
        gif = Image.open(candidate)
        require(gif.n_frames == len(frames), 'Encoded frame count mismatch')
        require(gif.info.get('loop') == 0, 'Loop mismatch')
        contact = Image.new('RGB', (size[0]*2, size[1]*((len(frames)+1)//2)), '#eeeeee')
        fixed_text = None
        for i,f in enumerate(frames):
            gif.seek(i)
            dec = gif.convert('RGBA')
            require(gif.info.get('duration') == durations[i] and gif.disposal_method == 2, 'Timing/disposal mismatch')
            require(np.array_equal(np.array(dec.getchannel('A'))>0, np.array(f.getchannel('A'))>=threshold), 'Decoded alpha mismatch')
            decoded_text = dec.crop((tx,ty,tx2,ty2))
            if expected_height is not None:
                check_glyph_height(decoded_text, expected_height, metrics['maximum_black_height'])
            region = np.array(decoded_text)
            if fixed_text is None:
                fixed_text = region
            require(np.array_equal(region, fixed_text), 'Text changes between frames')
            dec.save(checks / f'decoded-{i:02d}.png')
            pos = (i%2*size[0], i//2*size[1])
            contact.paste(dec, pos, dec)
            ImageDraw.Draw(contact).rectangle((pos[0]+left,pos[1]+top,pos[0]+right,pos[1]+bottom), outline='#00a0b0', width=2)
        contact.save(checks / 'contact.png')
        require(candidate.stat().st_size <= c['max_bytes'], 'GIF exceeds configured file-size limit')
        gif.close()
        destination = resolve(c['output'])
        require(destination.parent.name == 'output', 'Deliverables must use shared output directory')
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = destination.with_suffix('.pending')
        staging.write_bytes(candidate.read_bytes())
        os.replace(staging, destination)
        report.update(status='technical_checks_passed', output=str(destination), output_sha256=digest(destination),
                      visual_approval='pending; inspect decoded contact sheet and animation')
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        (checks / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    args = parser.parse_args()
    print(json.dumps(build(args.config), ensure_ascii=False, indent=2))
