"""Texture text replacement framework.
A spec is a dict:
  arch  : path under orig/ to the .spc (e.g. '01_salmon_team/data/win/flash/ainori/ainori_title_sele_US.spc')
  inner : optional name of nested .spc inside arch
  tex   : texture name inside srd
  text  : Russian text ('\n' for line breaks)
  font  : key in FONTS
  plus optional style keys: fill (rgba or 'auto'), stroke (width), stroke_fill, shadow (dx,dy,rgba),
        glow (radius, rgba), gradient ((rgb_top),(rgb_bottom)), align ('center'|'left'|'right'),
        box (x0,y0,x1,y1) target area (default: original ink bbox), clear ('all'|'box'|None),
        fit ('height'|'box'), cap (cap height px), maxw, rotate (deg), arc (radius, for circular text),
        tracking (px), line_gap, keep (list of boxes to keep from original), bg (rgba to fill box)
build_all(specs) -> writes modified spc files to build/data/win/... preserving relative path.
"""
import sys, os, io, json, math
sys.path.insert(0, os.path.dirname(__file__))
from drv3 import *
from srdtex import textures, decode, replace, replace_append
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), '..')
F = lambda p: os.path.join(ROOT, 'work', p)
FONTS = {
    'mpr': F('fontdl/mpr_full_700.ttf'), 'mpr5': F('fontdl/mpr_full_500.ttf'),
    'days': F('fonts/days-one_400.ttf'), 'russo': F('fonts/russo-one_400.ttf'),
    'rubik': F('fonts/rubik_700.ttf'), 'rubik9': F('fonts/rubik_900.ttf'), 'rubik5': F('fonts/rubik_500.ttf'),
    'exo': F('fonts/exo-2_800.ttf'), 'exo9': F('fonts/exo-2_900.ttf'), 'exo6': F('fonts/exo-2_600.ttf'),
    'oswald': F('fonts/oswald_700.ttf'), 'oswald5': F('fonts/oswald_500.ttf'),
    'seymour': F('fonts/seymour-one_400.ttf'), 'monoone': F('fonts/rubik-mono-one_400.ttf'),
    'pixel': F('fonts/press-start-2p_400.ttf'), 'comfortaa': F('fonts/comfortaa_700.ttf'),
    'neucha': F('fonts/neucha_400.ttf'), 'marck': F('fonts/marck-script_400.ttf'),
    'ubuntu': F('fonts/ubuntu_700.ttf'), 'ptn': F('fonts/pt-sans-narrow_700.ttf'),
    'montalt': F('fonts/montserrat-alternates_800.ttf'), 'kelly': F('fonts/kelly-slab_400.ttf'),
    'vibes': F('fonts3/greatvibes.ttf'), 'philo': F('fonts3/philosopher_700_normal.ttf'),
    'philoi': F('fonts3/philosopher_700_italic.ttf'), 'philo4': F('fonts3/philosopher_400_normal.ttf'),
    'ptserif': F('fonts3/ptserif_700.ttf'), 'amatic': F('fonts3/amatic_700.ttf'),
    'roboto': F('fonts3/roboto_700.ttf'), 'roboto5': F('fonts3/roboto_500.ttf'), 'roboto4': F('fonts3/roboto_400.ttf'),
    'mpr4': F('fonts3/mpr_400.ttf'), 'mpr8': F('fonts3/mpr_800.ttf'), 'mpr9': F('fonts3/mpr_900.ttf'),
    'rubik4': F('fonts/rubik_400.ttf'),
}
SS = 4


def ink_bbox(im, thr=24):
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > thr)
    if len(xs) == 0:
        return (0, 0, im.width, im.height)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def dominant_color(im):
    a = np.array(im)
    m = a[:, :, 3] > 200
    if m.sum() == 0:
        return (255, 255, 255, 255)
    px = (a[m][:, :3] // 8).astype(np.int32)
    key = px[:, 0] * 1024 + px[:, 1] * 32 + px[:, 2]
    v, c = np.unique(key, return_counts=True)
    k = v[c.argmax()]
    return (int(k // 1024 * 8 + 4), int(k // 32 % 32 * 8 + 4), int(k % 32 * 8 + 4), 255)


def render_lines(text, font, size, tracking=0, line_gap=1.0):
    """Render text mask (L) at supersampled size; returns mask image tight-cropped horizontally,
    with vertical extent from cap-top of first line to baseline of last line."""
    f = ImageFont.truetype(font, size)
    lines = text.split('\n')
    asc = f.getbbox('НH', anchor='ls')[1]  # negative cap height
    cap = -asc
    lh = int(round(cap * 1.45 * line_gap)) if len(lines) > 1 else cap
    widths = []
    for ln in lines:
        if tracking:
            w = sum(f.getlength(ch) for ch in ln) + tracking * SS * max(0, len(ln) - 1)
        else:
            w = f.getlength(ln)
        widths.append(w)
    W = int(max(widths) + size)
    desc = int(size * 0.35)
    H = cap + lh * (len(lines) - 1) + desc + int(size * 0.3)
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    top = int(size * 0.3)
    for k, ln in enumerate(lines):
        y = top + cap + k * lh
        x = (W - widths[k]) / 2
        if tracking:
            for ch in ln:
                d.text((x, y), ch, font=f, fill=255, anchor='ls'); x += f.getlength(ch) + tracking * SS
        else:
            d.text((x, y), ln, font=f, fill=255, anchor='ls')
    return m, top, cap, lh


def render_jitter(text, font, size, jit=0.08, rot=6, seed=1, tracking=0):
    """Одна строка, буквы «прыгают»: случайный сдвиг по вертикали и наклон (стиль подписей эффектов)."""
    import random
    rnd = random.Random(seed)
    f = ImageFont.truetype(font, size)
    cap = -f.getbbox('НH', anchor='ls')[1]
    pad = int(size * 0.6)
    W = int(sum(f.getlength(ch) for ch in text) + tracking * SS * len(text) + 2 * pad)
    H = cap + 2 * pad
    m = Image.new('L', (W, H), 0)
    x = pad; base = pad + cap
    for k, ch in enumerate(text):
        adv = f.getlength(ch)
        if ch != ' ':
            g = Image.new('L', (int(adv + 2 * pad), H), 0)
            ImageDraw.Draw(g).text((pad, base), ch, font=f, fill=255, anchor='ls')
            dy = int(rnd.uniform(-jit, jit) * cap) if k else int(-abs(jit) * cap * 0.5)
            g = g.rotate(rnd.uniform(-rot, rot), resample=Image.BICUBIC, center=(pad + adv / 2, base - cap / 2))
            sub = np.array(m.crop((int(x - pad), dy, int(x - pad) + g.width, dy + H)))
            if sub.shape == np.array(g).shape:
                m.paste(Image.fromarray(np.maximum(sub, np.array(g))), (int(x - pad), dy))
        x += adv + tracking * SS
    return m, pad, cap, cap


def orig_gradient(orig_im, box=None, erode=3, bins=12, lum_min=None):
    """Вертикальный градиент заливки исходного текста (без обводки): список цветов сверху вниз."""
    import cv2
    a = np.array(orig_im).astype(np.float32)
    m = (a[:, :, 3] > 200).astype(np.uint8)
    if box:
        bm = np.zeros_like(m); bm[int(box[1]):int(box[3]), int(box[0]):int(box[2])] = 1; m &= bm
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    inner = dist > erode
    if lum_min is not None:
        inner &= a[:, :, :3].mean(2) >= lum_min
    if inner.sum() < 30:
        inner = m > 0
    ys = np.where(inner)[0]
    y0, y1 = ys.min(), ys.max() + 1
    rows = np.arange(a.shape[0])[:, None] * np.ones((1, a.shape[1]))
    stops = []
    for i in range(bins):
        lo = y0 + (y1 - y0) * i / bins; hi = y0 + (y1 - y0) * (i + 1) / bins
        sel = inner & (rows >= lo) & (rows < hi)
        if sel.sum() < 3:
            continue
        stops.append(tuple(int(v) for v in np.median(a[sel][:, :3], axis=0)))
    return stops or [(255, 255, 255)]


def dot_layer(orig_im, spec):
    """Огоньки (ряд круглых точек) из оригинала: находим, достраиваем пропуски вдоль прямой, возвращаем слой."""
    import cv2
    a = np.array(orig_im)
    al = (a[:, :, 3] > spec.get('dot_thr', 110)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(al, 8)
    lo, hi = spec.get('dot_size', (6, 26))
    dots = []
    for i in range(1, n):
        x, y, w, h, ar = st[i]
        if lo <= w <= hi and lo <= h <= hi and 0.7 <= w / h <= 1.45 and ar >= 0.5 * w * h:
            dots.append((cen[i][0], cen[i][1], i, w, h))
    W, H = orig_im.size
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if len(dots) < 3:
        return out
    g = spec.get('dot_glow', 4)
    sprites = []
    for cx, cy, i, w, h in dots:
        r = int(max(w, h) / 2 + g)
        x0, y0 = int(round(cx)) - r, int(round(cy)) - r
        box = (max(0, x0), max(0, y0), min(W, x0 + 2 * r + 1), min(H, y0 + 2 * r + 1))
        sp = orig_im.crop(box)
        # только сама точка + её свечение (без соседних букв)
        m = (lab[box[1]:box[3], box[0]:box[2]] == i).astype(np.uint8) * 255
        m = np.array(dilate(Image.fromarray(m), g))
        spa = np.array(sp); spa[:, :, 3] = (spa[:, :, 3].astype(np.float32) * m / 255).astype(np.uint8)
        sprites.append(((cx, cy), Image.fromarray(spa), box))
    for (cx, cy), sp, box in sprites:
        out.alpha_composite(sp, (box[0], box[1]))
    if spec.get('dot_fill', True):
        P = np.array([(d[0], d[1]) for d in dots])
        # прямая через точки (по x), шаг — медиана расстояний до ближайшей
        A = np.vstack([P[:, 0], np.ones(len(P))]).T
        k, b = np.linalg.lstsq(A, P[:, 1], rcond=None)[0]
        res = np.abs(P[:, 1] - (k * P[:, 0] + b))
        good = res < 6
        P = P[good]
        if len(P) >= 3:
            order = np.argsort(P[:, 0]); P = P[order]
            dd = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
            step = np.median(dd)
            tmpl = sorted(sprites, key=lambda s_: -int(np.array(s_[1])[:, :, 3].astype(np.int64).sum()))[len(sprites) // 2][1]
            for j in range(len(P) - 1):
                gap = dd[j]
                m_ = int(round(gap / step)) - 1
                for t in range(1, m_ + 1):
                    x = P[j, 0] + (P[j + 1, 0] - P[j, 0]) * t / (m_ + 1)
                    y = P[j, 1] + (P[j + 1, 1] - P[j, 1]) * t / (m_ + 1)
                    out.alpha_composite(tmpl, (int(round(x - tmpl.width / 2)), int(round(y - tmpl.height / 2))))
    return out


def make_text_layer(spec, size_wh, box):
    """Return RGBA layer (texture size) with styled text fitted into box."""
    W, H = size_wh
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    text = spec['text']
    font = FONTS[spec.get('font', 'mpr')]
    nlines = text.count('\n') + 1
    stroke = spec.get('stroke', 0)
    pad = stroke + (spec.get('glow', (0,))[0] if spec.get('glow') else 0)
    # cap height target
    cap_t = spec.get('cap')
    if cap_t is None:
        if nlines == 1:
            cap_t = (bh - 2 * pad) * spec.get('capratio', 0.72)
        else:
            cap_t = (bh - 2 * pad) / (1 + 1.45 * spec.get('line_gap', 1.0) * (nlines - 1)) * spec.get('capratio', 0.95)
    # find font size giving that cap height
    ref = ImageFont.truetype(font, 1000)
    capref = -ref.getbbox('НH', anchor='ls')[1]
    size = max(4, int(round(cap_t * SS * 1000 / capref)))
    if spec.get('jitter'):
        m, top, cap, lh = render_jitter(text, font, size, spec['jitter'], spec.get('jrot', 6), spec.get('seed', 1), spec.get('tracking', 0))
    else:
        m, top, cap, lh = render_lines(text, font, size, spec.get('tracking', 0), spec.get('line_gap', 1.0))
    a = np.array(m)
    xs = np.where(a.max(0) > 0)[0]
    if len(xs) == 0:
        return Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = m.crop((xs.min(), 0, xs.max() + 1, m.height))
    if spec.get('italic'):
        sh = spec['italic']; extra = int(abs(sh) * m.height) + 2
        m = m.transform((m.width + extra, m.height), Image.AFFINE, (1, sh, -sh * m.height if sh > 0 else 0, 0, 1, 0), resample=Image.BICUBIC)
        a2 = np.array(m); xs2 = np.where(a2.max(0) > 0)[0]
        if len(xs2): m = m.crop((xs2.min(), 0, xs2.max() + 1, m.height))
    # scale to target
    sx = 1.0 / SS
    tw = m.width * sx
    maxw = spec.get('maxw', bw - 2 * pad)
    hscale = min(1.0, maxw / tw) if tw > 0 else 1
    hscale = min(hscale, spec.get('hscale', 1.0))
    # слишком узко — уменьшаем шрифт целиком, а не только сжимаем по ширине
    vscale = 1.0
    minh = spec.get('minh', 0)
    if minh and hscale < minh:
        vscale = hscale / minh
        hscale = minh * vscale
    nw = max(1, int(round(tw * hscale)))
    nh = max(1, int(round(m.height * sx * vscale)))
    m = m.resize((nw, nh), Image.LANCZOS)
    top_px = top * sx * vscale
    block_h = (cap + lh * (nlines - 1)) * sx * vscale
    # position
    align = spec.get('align', 'center')
    if align == 'left':
        px = x0 + pad
    elif align == 'right':
        px = x1 - pad - nw
    else:
        px = x0 + (bw - nw) / 2
    valign = spec.get('valign', 'center')
    if valign == 'top':
        py = y0 + pad - top_px
    elif valign == 'bottom':
        py = y1 - pad - block_h - top_px
    else:
        py = y0 + (bh - block_h) / 2 - top_px
    px += spec.get('dx', 0); py += spec.get('dy', 0)
    mask = Image.new('L', (W, H), 0)
    mask.paste(m, (int(round(px)), int(round(py))))
    return style(mask, spec, (W, H))


def style(mask, spec, size):
    W, H = size
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if spec.get('embolden'):
        mask = dilate(mask, spec['embolden'])
    if spec.get('hollow'):
        # неоновые трубки: только контур букв
        hw = spec['hollow']
        outer = np.array(dilate(mask, hw / 2)).astype(np.int32)
        import cv2
        inner = cv2.erode((np.array(mask) > 127).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=max(1, int(hw / 2)))
        ring = np.clip(outer - inner.astype(np.int32) * 255, 0, 255).astype(np.uint8)
        mask = Image.fromarray(ring)
    fill = spec.get('fill', (255, 255, 255, 255))
    if spec.get('glow'):
        r, col = spec['glow']
        g = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(r))
        ga = np.clip(np.array(g).astype(np.float32) * spec.get('glow_gain', 2.0), 0, 255).astype(np.uint8)
        gl = Image.new('RGBA', (W, H), col[:3] + (0,)); gl.putalpha(Image.fromarray(ga))
        layer = Image.alpha_composite(layer, gl)
    if spec.get('shadow'):
        dx, dy, col = spec['shadow']
        sm = Image.new('L', mask.size, 0); sm.paste(mask, (dx, dy))  # без заворота через край
        sw = max([w for w, _ in spec.get('strokes', [])] + [spec.get('stroke', 0)])
        if sw:
            sm = dilate(sm, sw)
        sl = Image.new('RGBA', (W, H), col[:3] + (0,)); sl.putalpha(Image.fromarray((np.array(sm) * (col[3] / 255)).astype(np.uint8)))
        layer = Image.alpha_composite(layer, sl)
    for st in spec.get('strokes', []) or ([(spec['stroke'], spec.get('stroke_fill', (0, 0, 0, 255)))] if spec.get('stroke') else []):
        w, col = st
        sm = dilate(mask, w)
        sl = Image.new('RGBA', (W, H), col[:3] + (0,)); sl.putalpha(Image.fromarray((np.array(sm) * (col[3] / 255)).astype(np.uint8)))
        layer = Image.alpha_composite(layer, sl)
    fmask = mask
    if spec.get('gradient'):
        stops = spec['gradient']
        a = np.array(mask); ys, xs = np.where(a > 0)
        top, bot = (ys.min(), ys.max()) if len(ys) else (0, H)
        t = np.clip((np.arange(H) - top) / max(1, bot - top), 0, 1)
        pos = np.linspace(0, 1, len(stops))
        grad = np.zeros((H, W, 4), np.uint8)
        for k in range(3):
            col = np.interp(t, pos, [c[k] for c in stops])
            grad[:, :, k] = col[:, None].astype(np.uint8)
        grad[:, :, 3] = a
        layer = Image.alpha_composite(layer, Image.fromarray(grad))
    else:
        fl = Image.new('RGBA', (W, H), tuple(fill[:3]) + (0,))
        fl.putalpha(Image.fromarray((np.array(mask) * (fill[3] / 255 if len(fill) > 3 else 1)).astype(np.uint8)))
        layer = Image.alpha_composite(layer, fl)
    if spec.get('first_fill'):
        # первая буква другим цветом (как «U» в Ultimate)
        a = np.array(fmask); cols = (a > 100).any(0)
        xs = np.where(cols)[0]
        if len(xs):
            x0 = xs[0]; x1 = x0
            while x1 < W and cols[x1]: x1 += 1
            col = spec['first_fill']
            fa = a.copy(); fa[:, :x0] = 0; fa[:, x1:] = 0
            fl = Image.new('RGBA', (W, H), tuple(col[:3]) + (0,)); fl.putalpha(Image.fromarray(fa))
            layer = Image.alpha_composite(layer, fl)
    if spec.get('halftone'):
        # растровые точки поверх заливки (как в логотипе Плана развития)
        sp, rmax, al = spec['halftone']
        a = np.array(fmask)
        ys = np.where(a.max(1) > 0)[0]
        if len(ys):
            t0, t1 = ys.min(), ys.max()
            S2 = 4
            big = Image.new('L', (W * S2, H * S2), 0); d = ImageDraw.Draw(big)
            for yy in range(int(t0), int(t1) + 1, sp):
                r = rmax * (0.25 + 0.75 * (yy - t0) / max(1, t1 - t0))
                off = (sp / 2) if ((yy - t0) // sp) % 2 else 0
                for xx in np.arange(off, W, sp):
                    d.ellipse([(xx - r) * S2, (yy - r) * S2, (xx + r) * S2, (yy + r) * S2], fill=255)
            dm = np.array(big.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
            ha = (dm * a * al).astype(np.uint8)
            hl = Image.new('RGBA', (W, H), (255, 255, 255, 0)); hl.putalpha(Image.fromarray(ha))
            layer = Image.alpha_composite(layer, hl)
    return layer


def dilate(mask, w):
    """Round anti-aliased dilation of an L mask by w pixels (via distance transform)."""
    if w <= 0:
        return mask
    import cv2
    a = np.array(mask)
    inside = (a > 127).astype(np.uint8)
    dist = cv2.distanceTransform(1 - inside, cv2.DIST_L2, 5)
    out = np.clip(w + 0.5 - dist, 0, 1)
    out = np.maximum(out, a.astype(np.float32) / 255)
    return Image.fromarray((out * 255).astype(np.uint8))


def apply_spec(orig_im, spec):
    W, H = orig_im.size
    if spec.get('fill') == 'auto':
        spec = dict(spec, fill=dominant_color(orig_im))
    if spec.get('gradient') == 'orig':
        spec = dict(spec, gradient=orig_gradient(orig_im, spec.get('grad_box'), spec.get('grad_erode', 3), spec.get('grad_bins', 12), spec.get('grad_lum')))
    if spec.get('custom'):
        return spec['custom'](orig_im, spec)
    box = spec.get('box') or ink_bbox(orig_im)
    if spec.get('expand'):
        e = spec['expand']; box = (max(0, box[0] - e), max(0, box[1] - e), min(W, box[2] + e), min(H, box[3] + e))
    if spec.get('fill') == 'auto':
        spec = dict(spec, fill=dominant_color(orig_im))
    if spec.get('bg') == 'auto':
        a = np.array(orig_im).astype(np.int32)
        op = Image.fromarray(((a[:, :, 3] > 200) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(spec.get('erode', 9)))
        er = np.array(op) > 0
        px = a[er][:, :3]
        key = (px[:, 0] // 8) * 1024 + (px[:, 1] // 8) * 32 + px[:, 2] // 8
        v, c = np.unique(key, return_counts=True); k = v[c.argmax()]
        bgc = np.array([k // 1024 * 8 + 4, k // 32 % 32 * 8 + 4, k % 32 * 8 + 4])
        bgm = (np.abs(a[:, :, :3] - bgc).sum(2) <= spec.get('bgthr', 90)) & (a[:, :, 3] > 200)
        yb, xb = np.where(bgm)
        sh = spec.get('shrink', 4)
        inner = np.zeros_like(bgm); inner[yb.min() + sh:yb.max() + 1 - sh, xb.min() + sh:xb.max() + 1 - sh] = True
        diff = (~bgm) & inner
        ys, xs = np.where(diff)
        if len(xs):
            e = spec.get('bgexp', 3)
            tb = (max(0, xs.min() - e), max(0, ys.min() - e), min(W, xs.max() + 1 + e), min(H, ys.max() + 1 + e))
            area = (xb.min() + sh, yb.min() + sh, xb.max() + 1 - sh, yb.max() + 1 - sh)
            spec = dict(spec, clear='box', clearbox=tb, bg=tuple(int(x) for x in bgc) + (255,), box=spec.get('box') or tb)
            if 'textbox' not in spec:
                cx = (tb[0] + tb[2]) / 2; half = min(cx - area[0] - 2, area[2] - 2 - cx)
                spec['textbox'] = (cx - half, tb[1], cx + half, tb[3])
            box = spec['box']
    clear = spec.get('clear', 'all')
    if clear == 'all':
        base = Image.new('RGBA', (W, H), tuple(spec.get('basefill', (0, 0, 0, 0))))
    elif clear == 'box':
        base = orig_im.copy()
        cb = spec.get('clearbox', box)
        bg = spec.get('bg', (0, 0, 0, 0))
        ImageDraw.Draw(base).rectangle([cb[0], cb[1], cb[2] - 1, cb[3] - 1], fill=bg)
    else:
        base = orig_im.copy()
    if spec.get('under'):
        base = Image.alpha_composite(base, spec['under'](orig_im, spec))
    tb = spec.get('textbox')
    if tb is None:
        mg = spec.get('margin', 3)
        if spec.get('widen', True):
            align = spec.get('align', 'center')
            if align == 'left':
                tb = (box[0], box[1], W - mg, box[3])
            elif align == 'right':
                tb = (mg, box[1], box[2], box[3])
            else:
                cx = (box[0] + box[2]) / 2; half = min(cx - mg, W - mg - cx)
                tb = (cx - half, box[1], cx + half, box[3])
        else:
            tb = box
    if spec.get('grow'):
        # ширина надписи — не больше исходной × grow (иначе упирается в края)
        ib = ink_bbox(orig_im)
        lim = (ib[2] - ib[0]) * spec['grow']
        if tb[2] - tb[0] > lim:
            cx = {'left': tb[0] + lim / 2, 'right': tb[2] - lim / 2}.get(spec.get('align', 'center'), (tb[0] + tb[2]) / 2)
            tb = (cx - lim / 2, tb[1], cx + lim / 2, tb[3])
    layer = make_text_layer(spec, (W, H), tb)
    if spec.get('rotate'):
        cx = (box[0] + box[2]) / 2; cy = (box[1] + box[3]) / 2
        layer = layer.rotate(spec['rotate'], resample=Image.BICUBIC, center=(cx, cy))
    return finish(orig_im, spec, Image.alpha_composite(base, layer))


def finish(orig_im, spec, out):
    """Вернуть из оригинала украшения: огоньки (keep_dots) и прямоугольники keep_boxes."""
    for kb in spec.get('keep_boxes', []):
        out.alpha_composite(orig_im.crop(kb), (kb[0], kb[1]))
    if spec.get('keep_dots'):
        out = Image.alpha_composite(out, dot_layer(orig_im, spec))
    return out


def load_arch(arch):
    return spc_read(open(os.path.join(ROOT, 'orig', arch), 'rb').read())


def out_path(arch):
    rel = arch.split('/', 1)[1] if arch.split('/', 1)[0][:2].isdigit() else arch
    if rel.startswith('1/'):
        rel = 'BYNAME/' + rel[2:]
    return os.path.join(ROOT, 'build', rel)


def expand_specs(specs):
    ix = json.load(open(os.path.join(ROOT, 'work/tex/index.json')))
    loc = {}
    for x in ix:
        loc.setdefault(x[2], set()).add(x[0].replace('orig/', '', 1))
    out = []
    for s in specs:
        if s.get('arch'):
            out.append(s); continue
        archs = sorted(loc.get(s['tex'], []))
        archs = [a for a in archs if not a.startswith('00_test')]
        if s.get('only'):
            archs = [a for a in archs if any(o in a for o in s['only'])]
        if not archs:
            print('NOT FOUND', s['tex'])
        for a in archs:
            out.append(dict(s, arch=a))
    return out


def build_all(specs, preview=None, only=None):
    specs = expand_specs(specs)
    by = {}
    for s in specs:
        by.setdefault(s['arch'], []).append(s)
    previews = []
    for arch, ss in by.items():
        if only and not any(o in arch for o in only):
            continue
        spc = load_arch(arch)
        groups = {}
        for s in ss:
            groups.setdefault(s.get('inner'), []).append(s)
        for inner, sl in groups.items():
            if inner:
                ie = [e for e in spc['entries'] if e.name == inner][0]
                tgt = spc_read(ie.data)
            else:
                tgt = spc
            E = {e.name: e for e in tgt['entries']}
            srdn = [n for n in E if n.endswith('.srd')]
            done = set()
            for sn in srdn:
                vn = sn + 'v'
                if vn not in E:
                    continue
                ts = {t['name']: t for t in textures(E[sn].data)}
                new = {}
                for s in sl:
                    if s['tex'] in ts:
                        t = ts[s['tex']]
                        oi = decode(t, E[vn].data)
                        ni = apply_spec(oi, s)
                        new[s['tex']] = ni
                        previews.append((arch.split('/')[-1] + (':' + inner if inner else '') + ':' + s['tex'], oi, ni))
                        done.add(s['tex'])
                if new:
                    srd2, tail = replace_append(E[sn].data, len(E[vn].data), new)
                    E[sn].data = srd2; E[vn].append_tail = tail
            miss = [s['tex'] for s in sl if s['tex'] not in done]
            if miss:
                print('MISSING', arch, inner, miss)
            if inner:
                ie.data = spc_write(tgt, compress=True)
        op = out_path(arch)
        os.makedirs(os.path.dirname(op), exist_ok=True)
        open(op, 'wb').write(spc_write(spc, compress=True))
    if preview and previews:
        make_preview(previews, preview)
    return previews


def make_preview(previews, path, maxw=1400):
    rows = []; seen = set()
    for name, a, b in previews:
        key = name.split(':')[-1]
        if key in seen:
            continue
        seen.add(key)
        s = min(1.0, 600 / max(a.width, 1), 300 / max(a.height, 1))
        aa = a.resize((max(1, int(a.width * s)), max(1, int(a.height * s))))
        bb = b.resize(aa.size)
        rows.append((name, aa, bb))
    H = sum(max(r[1].height, 14) + 18 for r in rows)
    W = min(maxw, max(r[1].width * 2 + 20 for r in rows))
    C = Image.new('RGBA', (W, H), (70, 70, 90, 255)); d = ImageDraw.Draw(C); y = 0
    for name, a, b in rows:
        d.text((0, y), name, fill=(255, 255, 0, 255))
        C.alpha_composite(a, (0, y + 14)); C.alpha_composite(b, (a.width + 20, y + 14))
        y += a.height + 18
    C.save(path)


def arc_text(orig, spec):
    """Circular text, clockwise, letter tops pointing outward. spec['arcs']=[(text,a0,a1)], spec r0 (baseline radius),
    cap (cap height px), center (cx,cy), font, fill, stroke..."""
    W, H = orig.size
    cx, cy = spec.get('center', (W / 2, H / 2))
    font = FONTS[spec.get('font', 'mpr')]
    ref = ImageFont.truetype(font, 1000); capref = -ref.getbbox('Н', anchor='ls')[1]
    size = int(round(spec['cap'] * SS * 1000 / capref))
    f = ImageFont.truetype(font, size)
    mask = Image.new('L', (W * SS, H * SS), 0)
    r0 = spec['r0'] * SS
    for text, a0, a1 in spec['arcs']:
        advs = [f.getlength(ch) for ch in text]
        total = sum(advs)
        span = math.radians((a1 - a0) % 360 or 360)
        # arc length available at text middle radius
        rm = r0 + spec['cap'] * SS / 2
        natural = total / rm
        scale = span / natural if spec.get('stretch', True) else 1.0
        scale = min(scale, spec.get('maxstretch', 1.6))
        used = natural * scale
        start = math.radians(a0) + (span - used) / 2
        ang = start
        for ch, adv in zip(text, advs):
            da = adv / rm * scale
            mid = ang + da / 2
            # render glyph upright then rotate
            g = Image.new('L', (size * 2, size * 2), 0)
            ImageDraw.Draw(g).text((size, size), ch, font=f, fill=255, anchor='ms')
            # glyph baseline center at (size,size); rotate so that 'up' points outward
            deg = -(math.degrees(mid) + 90)
            g = g.rotate(deg, resample=Image.BICUBIC, center=(size, size))
            px = cx * SS + r0 * math.cos(mid) - size
            py = cy * SS + r0 * math.sin(mid) - size
            mask.paste(Image.fromarray(np.maximum(np.array(mask.crop((int(px), int(py), int(px) + 2 * size, int(py) + 2 * size))), np.array(g))), (int(px), int(py)))
            ang += da
    mask = mask.resize((W, H), Image.LANCZOS)
    layer = style(mask, spec, (W, H))
    return Image.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 0)), layer)


def layers_custom(orig, spec):
    """spec['layers'] = list of sub-specs (each with text, box, style...). Base cleared unless clear=None."""
    W, H = orig.size
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0)) if spec.get('clear', 'all') == 'all' else orig.copy()
    for L in spec['layers']:
        sub = {k: v for k, v in L.items() if v is not None}
        if sub.get('fill') == 'auto':
            sub['fill'] = dominant_color(orig)
        if sub.get('gradient') == 'orig':
            sub['gradient'] = orig_gradient(orig, sub.get('grad_box'), sub.get('grad_erode', 3), sub.get('grad_bins', 12), sub.get('grad_lum'))
        lay = make_text_layer(sub, (W, H), sub['box'])
        if sub.get('rotate'):
            b = sub['box']; lay = lay.rotate(sub['rotate'], resample=Image.BICUBIC, center=((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
        base = Image.alpha_composite(base, lay)
    return finish(orig, spec, base)


def word_groups(im, gap=6, thr=30):
    a = np.array(im)[:, :, 3]
    cols = (a > thr).any(0)
    runs = []; x = 0; W = len(cols)
    while x < W:
        if cols[x]:
            s = x
            while x < W and cols[x]: x += 1
            runs.append([s, x])
        x += 1
    groups = []
    for r in runs:
        if groups and r[0] - groups[-1][1] < gap:
            groups[-1][1] = r[1]
        else:
            groups.append(list(r))
    out = []
    for g in groups:
        ys = np.where((a[:, g[0]:g[1]] > thr).any(1))[0]
        out.append((g[0], int(ys.min()), g[1], int(ys.max()) + 1))
    return out


def words_custom(orig, spec):
    """Replace text word-groups, keep icon groups. spec['words'] = list of texts for each text segment (in order);
    spec['segments'] optional explicit list of (x0,x1) text spans. Icons auto = groups with width < 1.5*height."""
    W, H = orig.size
    base = orig.copy()
    if spec.get('segments'):
        segs = spec['segments']
    else:
        gs = word_groups(orig, spec.get('gap', 6))
        # merge consecutive non-icon groups into text segments
        segs = []; cur = None
        for g in gs:
            w = g[2] - g[0]; h = g[3] - g[1]
            icon = w < 1.6 * h and len(segs) + (1 if cur else 0) < 99 and spec.get('icons', True) and (g[2] - g[0]) > 0 and h > 0 and w >= 0.7 * h
            if icon:
                if cur: segs.append(cur); cur = None
            else:
                cur = [g[0], g[2]] if cur is None else [cur[0], g[2]]
        if cur: segs.append(cur)
    texts = spec['words']
    gsall = word_groups(orig, spec.get('gap', 6))
    ybox = (min(g[1] for g in gsall), max(g[3] for g in gsall))
    for i, (x0, x1) in enumerate(segs[:len(texts)]):
        ImageDraw.Draw(base).rectangle([x0 - 1, 0, x1, H], fill=(0, 0, 0, 0))
        # available width: until next segment/icon or texture end
        nxt = W - 2
        for g in gsall:
            if g[0] > x1 + 1:
                nxt = g[0] - 4; break
        sub = dict(spec, text=texts[i], align='left')
        sub.pop('custom', None)
        if sub.get('fill') == 'auto':
            sub['fill'] = dominant_color(orig)
        lay = make_text_layer(sub, (W, H), (x0, ybox[0], max(x1, nxt if spec.get('extend', True) else x1), ybox[1]))
        base = Image.alpha_composite(base, lay)
    return base


def stamp_custom(orig, spec):
    """Rotated rubber stamp: frame + text, grunge."""
    W, H = orig.size
    S2 = 3
    big = Image.new('L', (W * S2, H * S2), 0); d = ImageDraw.Draw(big)
    x0, y0, x1, y1 = [v * S2 for v in spec['frame']]
    d.rounded_rectangle([x0, y0, x1, y1], radius=8 * S2, outline=255, width=int(spec.get('fw', 9) * S2))
    small = big.resize((W, H), Image.LANCZOS)
    sub = dict(spec); sub.pop('custom', None)
    tl = make_text_layer(dict(sub, fill=(255, 255, 255, 255), strokes=[], glow=None, shadow=None), (W, H), spec['tbox'])
    m = np.maximum(np.array(small), np.array(tl)[:, :, 3])
    rng = np.random.default_rng(1)
    noise = rng.random((H, W))
    m = (m * np.where(noise < spec.get('holes', 0.12), 0.25, 1.0)).astype(np.uint8)
    mask = Image.fromarray(m).rotate(spec.get('rotate_stamp', 20), resample=Image.BICUBIC, center=(W / 2, H / 2))
    col = spec.get('fill', (210, 210, 210, 255))
    out = Image.new('RGBA', (W, H), col[:3] + (0,)); out.putalpha(mask)
    return out


def blur_rgba(im, r):
    """Размытие RGBA без тёмной каймы (через premultiplied alpha)."""
    a = np.array(im).astype(np.float32)
    al = a[:, :, 3:4] / 255
    pm = np.concatenate([a[:, :, :3] * al, a[:, :, 3:4]], 2)
    import cv2
    out = cv2.GaussianBlur(pm.astype(np.float32), (0, 0), r)
    alpha = np.clip(out[:, :, 3:4], 1e-3, 255)
    rgb = np.clip(out[:, :, :3] / (alpha / 255), 0, 255)
    return np.concatenate([rgb, out[:, :, 3:4]], 2)


def aura_under(orig, spec):
    """Подложка для подписей эффектов: сильно размытый оригинал (облако того же цвета без букв)."""
    a = blur_rgba(orig, spec.get('aura_blur', 14))
    a[:, :, 3] = np.clip(a[:, :, 3] * spec.get('aura_gain', 1.3), 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def plate_custom(orig, spec):
    """Табличка (BONUS GAME!): текст стирается заливкой фона пластины по строкам, рамка остаётся."""
    W, H = orig.size
    a = np.array(orig).astype(np.float32)
    x0, y0, x1, y1 = spec['plate']
    lum = a[:, :, :3].mean(2)
    out = a.copy()
    S2 = 4
    m = Image.new('L', (W * S2, H * S2), 0)
    ImageDraw.Draw(m).rounded_rectangle([x0 * S2, y0 * S2, x1 * S2, y1 * S2], radius=spec.get('plate_r', 30) * S2, fill=255)
    m = np.array(m.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    flat = None
    if spec.get('plate_flat'):
        reg = a[y0:y1, x0:x1, :3].reshape(-1, 3).astype(np.int32) // 4
        key = reg[:, 0] * 4096 + reg[:, 1] * 64 + reg[:, 2]
        v, c = np.unique(key, return_counts=True); k = v[c.argmax()]
        flat = np.array([k // 4096 * 4 + 2, k // 64 % 64 * 4 + 2, k % 64 * 4 + 2], np.float32)
    for y in range(y0, y1):
        row = a[y, x0:x1]
        L = lum[y, x0:x1]
        if flat is not None:
            col = flat
        else:
            sel = L >= np.percentile(L, spec.get('plate_pct', 70))
            col = np.median(row[sel][:, :3], axis=0)
        out[y, :, :3] = out[y, :, :3] * (1 - m[y, :, None]) + col[None, :] * m[y, :, None]
    base = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    sub = dict(spec); sub.pop('custom', None)
    if sub.get('gradient') == 'orig':
        sub['gradient'] = orig_gradient(orig, sub.get('grad_box'), sub.get('grad_erode', 1), sub.get('grad_bins', 8), sub.get('grad_lum'))
    lay = make_text_layer(sub, (W, H), spec['tbox'])
    return Image.alpha_composite(base, lay)


def guide_custom(orig, spec):
    """Подсказки с кнопками: значки остаются, слова заново раскладываются по ширине (значок, слово, значок, слово)."""
    W, H = orig.size
    gs = word_groups(orig, spec.get('gap', 6))
    items = []
    if spec.get('segments'):
        # явные отрезки текста (x0, x1); всё остальное — значки
        a_ = np.array(orig)[:, :, 3]
        segs = spec['segments']
        cols = (a_ > 30).any(0)
        x = 0; W_ = len(cols)
        runs = []
        while x < W_:
            if cols[x]:
                s0 = x
                while x < W_ and cols[x]: x += 1
                runs.append((s0, x))
            x += 1
        icon_runs = [r for r in runs if not any(r[0] < x1 and r[1] > x0 for x0, x1 in segs)]
        # склеиваем близкие куски значков
        merged_ic = []
        for r in icon_runs:
            if merged_ic and r[0] - merged_ic[-1][1] < spec.get('gap', 6):
                merged_ic[-1] = (merged_ic[-1][0], r[1])
            else:
                merged_ic.append(r)
        els = [('icon', r) for r in merged_ic] + [('text', tuple(sg)) for sg in segs]
        els.sort(key=lambda e: e[1][0])
        for kind, (x0, x1) in els:
            ys = np.where((a_[:, x0:x1] > 30).any(1))[0]
            items.append((kind, (x0, int(ys.min()), x1, int(ys.max()) + 1)))
    else:
        for g in gs:
            w = g[2] - g[0]; h = g[3] - g[1]
            icon = (0.7 * h <= w < 1.6 * h)
            items.append(('icon' if icon else 'text', g))
    # объединяем соседние текстовые группы (слова одной подписи)
    merged = []
    for kind, g in items:
        if merged and kind == 'text' and merged[-1][0] == 'text':
            pg = merged[-1][1]; merged[-1] = ('text', (pg[0], min(pg[1], g[1]), g[2], max(pg[3], g[3])))
        else:
            merged.append((kind, g))
    texts = list(spec['words'])
    tys = [g for k, g in merged if k == 'text']
    ty0 = min(g[1] for g in tys); ty1 = max(g[3] for g in tys)
    cap = spec.get('cap') or (ty1 - ty0) * spec.get('capk', 0.74)
    gap_i = spec.get('gap_icon', 6); gap_w = spec.get('gap_word', 14)
    for attempt in range(8):
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        x = merged[0][1][0]; ti = 0
        for kind, g in merged:
            if kind == 'icon':
                if ti and x > g[0]:
                    pass
                out.alpha_composite(orig.crop((g[0], 0, g[2], H)), (int(x), 0))
                x += (g[2] - g[0]) + gap_i
            else:
                if ti >= len(texts):
                    continue
                sub = dict(spec, text=texts[ti], align='left', cap=cap, maxw=10000, hscale=spec.get('hscale', 1.0))
                sub.pop('custom', None)
                if sub.get('fill') == 'auto':
                    sub['fill'] = dominant_color(orig)
                lay = make_text_layer(sub, (W * 2, H), (x, ty0, W * 2, ty1))
                bb = ink_bbox(lay)
                out.alpha_composite(lay.crop((0, 0, W, H)))
                x = bb[2] + gap_w
                ti += 1
        if x - gap_w <= W - spec.get('margin', 4):
            return out
        cap *= 0.93
    return out
