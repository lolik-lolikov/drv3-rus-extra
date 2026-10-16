"""Перенос оформления надписи с оригинала на новую (по «аналогии»).

Для каждой точки новой надписи ищется точка оригинала с похожими признаками:
  d  — расстояние до края буквы (внутри +, снаружи −): даёт обводки, свечение, тени по толщине;
  n  — направление к краю (нормаль): даёт тени и блики с нужной стороны;
  v  — высота внутри строки (0 — верх букв, 1 — низ): даёт вертикальный градиент заливки;
  и цвет копируется из найденной точки. Узоры (полосы, «грязь», трещины) переносятся как похожий шум.

analog_custom(orig, spec) — custom-функция для tex_specs:
  текст раскладывается обычным make_text_layer (font, box, cap, italic, rotate...), из него берётся маска;
  spec['an_thr'] — порог альфы/яркости для маски оригинала (по умолчанию 128);
  spec['an_lum'] — маска оригинала по яркости (для DXT1 без альфы, фон чёрный);
  spec['an_core'] — толщина: 'auto' (подогнать полуширину штриха под оригинал) или число пикселей (+ расширить, − сузить);
  spec['an_R'] — сколько пикселей вокруг букв переносить (свечение/тени); spec['an_w'] — веса (d, v, n, x).
  spec['pixel'] = k — пиксель-арт: всё делается в разрешении 1/k и увеличивается без сглаживания."""
import numpy as np
import cv2
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree


def shape_mask(rgba, thr=128, lum=False):
    a = np.asarray(rgba)
    if lum:
        return a[:, :, :3].max(2) > thr
    return a[:, :, 3] > thr


def signed_dist(m):
    m8 = m.astype(np.uint8)
    din = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    dout = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 5)
    return np.where(m, din, -dout).astype(np.float32)


def normals(sd):
    g = cv2.GaussianBlur(sd, (0, 0), 1.5)
    gy, gx = np.gradient(g)
    n = np.hypot(gx, gy) + 1e-6
    return gx / n, gy / n


def half_width(m):
    """Медианная полуширина штриха: значения расстояния на «хребте» (локальные максимумы)."""
    m8 = m.astype(np.uint8)
    d = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    mx = cv2.dilate(d, np.ones((3, 3), np.uint8))
    ridge = (d >= mx - 1e-3) & (d > 0.8)
    v = d[ridge]
    return float(np.median(v)) if len(v) else 0.0


def line_bands(m, min_gap=2):
    """Горизонтальные полосы строк (по проекции)."""
    rows = m.any(1)
    bands = []; y = 0; H = len(rows)
    while y < H:
        if rows[y]:
            s = y
            while y < H and rows[y]: y += 1
            bands.append([s, y])
        y += 1
    out = []
    for b in bands:
        if out and b[0] - out[-1][1] <= min_gap:
            out[-1][1] = b[1]
        else:
            out.append(b)
    return out


def vpos(m, bands=None):
    H, W = m.shape
    bands = bands or line_bands(m)
    v = np.zeros((H, W), np.float32)
    if not bands:
        return v
    ys = np.arange(H, dtype=np.float32)
    # для каждой строки изображения — ближайшая полоса
    for y in range(H):
        best = min(bands, key=lambda b: 0 if b[0] <= y < b[1] else min(abs(y - b[0]), abs(y - b[1] + 1)))
        v[y, :] = (y - best[0]) / max(1, best[1] - best[0] - 1)
    return v


def transfer(orig, om, nm, R=24, w=(1.0, 22.0, 6.0, 0.0), bg=None, obands=None, nbands=None, seed=1):
    """orig: RGBA uint8 (H,W,4); om, nm: bool маски оригинала и новой надписи (одного размера)."""
    H, W = om.shape
    so = signed_dist(om); sn = signed_dist(nm)
    nxo, nyo = normals(so); nxn, nyn = normals(sn)
    vo = vpos(om, obands); vn = vpos(nm, nbands)
    xo = np.tile(np.arange(W, dtype=np.float32), (H, 1)) / max(W, 1)
    wd, wv, wn, wx = w
    selo = so > -R
    seln = sn > -R
    fo = np.stack([np.clip(so, -R, R) * wd, vo * wv, nxo * wn, nyo * wn, xo * wx], -1)[selo]
    fn = np.stack([np.clip(sn, -R, R) * wd, vn * wv, nxn * wn, nyn * wn, xo * wx], -1)[seln]
    co = np.asarray(orig)[selo]
    rng = np.random.default_rng(seed)
    if len(fo) > 600000:
        idx = rng.choice(len(fo), 600000, replace=False); fo = fo[idx]; co = co[idx]
    tree = cKDTree(fo)
    _, j = tree.query(fn, k=1, workers=-1)
    out = np.zeros((H, W, 4), np.uint8)
    if bg is not None:
        out[:, :] = bg
    out[seln] = co[j]
    # плавный переход на внешней границе зоны переноса
    if bg is None:
        fade = np.clip((sn + R) / 3.0, 0, 1)
        out[:, :, 3] = (out[:, :, 3].astype(np.float32) * fade).astype(np.uint8)
    return out


def match_width(nm, target_hw, max_iter=6):
    """Подогнать полуширину штриха новой маски к target_hw (дилатация/эрозия по расстоянию)."""
    hw = half_width(nm)
    delta = target_hw - hw
    if abs(delta) < 0.5:
        return nm
    m8 = nm.astype(np.uint8)
    if delta > 0:
        d = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 5)
        return nm | (d <= delta)
    d = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    return nm & (d > -delta)


def analog_custom(orig, spec):
    import texedit
    W, H = orig.size
    k = spec.get('pixel', 1)
    o = orig
    if k > 1:
        ox, oy = spec.get('pixel_off', (k // 2, k // 2))
        o = orig.crop((ox, oy, W, H)).resize(((W - ox) // k, (H - oy) // k), Image.NEAREST)
    Wl, Hl = o.size
    om = shape_mask(o, spec.get('an_thr', 128), spec.get('an_lum', False))
    # маска новой надписи (обычная раскладка текста; для пиксель-арта — в уменьшенном масштабе)
    s2 = dict(spec)
    for key in ('custom', 'gradient', 'glow', 'shadow', 'strokes', 'stroke', 'under', 'keep_dots', 'halftone', 'first_fill', 'hollow'):
        s2.pop(key, None)
    s2['fill'] = (255, 255, 255, 255)
    if k > 1:
        for key in ('box', 'textbox', 'cap', 'tracking'):
            if s2.get(key) is not None:
                v = s2[key]
                s2[key] = tuple(x / k for x in v) if isinstance(v, (tuple, list)) else v / k
        if 'base_y' in s2: s2['base_y'] /= k
    if s2.get('layers'):
        lay = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
        for L in s2['layers']:
            sub = {kk: vv for kk, vv in L.items()}
            sub['fill'] = (255, 255, 255, 255)
            for key in ('gradient', 'glow', 'shadow', 'strokes', 'stroke'):
                sub.pop(key, None)
            if k > 1:
                sub['box'] = tuple(x / k for x in sub['box'])
                if 'cap' in sub: sub['cap'] /= k
            l1 = texedit.make_text_layer(sub, (Wl, Hl), sub['box'])
            if sub.get('rotate'):
                b = sub['box']; l1 = l1.rotate(sub['rotate'], resample=Image.BICUBIC, center=((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
            lay = Image.alpha_composite(lay, l1)
    else:
        s2.pop('layers', None)
        tmp = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
        lay = texedit.apply_spec(tmp, dict(s2, clear='all', box=s2.get('box') or texedit.ink_bbox(o if not spec.get('an_lum') else Image.fromarray((om * 255).astype(np.uint8)).convert('RGBA'))))
    nm = np.asarray(lay)[:, :, 3] > 110
    core = spec.get('an_core', 'auto')
    if core == 'auto':
        nm = match_width(nm, half_width(om))
    elif core:
        nm = match_width(nm, half_width(nm) + core)
    bg = spec.get('an_bg')
    out = transfer(np.asarray(o), om, nm, R=spec.get('an_R', 24 // k if k > 1 else 24), w=spec.get('an_w', (1.0, 22.0, 6.0, 0.0)), bg=bg)
    img = Image.fromarray(out)
    if k > 1:
        big = img.resize((Wl * k, Hl * k), Image.NEAREST)
        full = Image.new('RGBA', (W, H), tuple(bg) if bg is not None else (0, 0, 0, 0))
        full.paste(big, spec.get('pixel_off', (k // 2, k // 2)))
        img = full
    if spec.get('an_post'):
        img = spec['an_post'](orig, spec, img)
    return img
