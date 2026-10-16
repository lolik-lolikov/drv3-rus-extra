"""Перенос оформления надписи оригинала на русский текст через таблицу (LUT).

Цвет каждой точки оформления оригинала зависит в основном от:
  d   — расстояния до края буквы (внутри +, снаружи −): обводки, фаска, свечение;
  v   — высоты внутри строки (0 — верх, 1 — низ): вертикальный градиент заливки;
  dir — направления от буквы: тени и блики со своей стороны;
  [ph] — фазы косых полос (для пиксельных надписей «Монолита»).
По оригиналу строится таблица медианных цветов по (d, v, dir, ph), маска новой надписи раскрашивается ею
(трилинейная интерполяция по d, v, dir). Толщина штриха новой надписи подгоняется под оригинал.

lut_custom(orig, spec) — custom-функция для tex_specs. Параметры spec:
  text, font, box/cap/capratio/italic/rotate/align/fit/... — раскладка как обычно (или layers=[...]);
  lx_thr     — порог альфы для маски оригинала (128); lx_lum=True — маска по яркости (DXT1 без альфы), lx_lum_thr;
  lx_core    — 'auto' (толщина как у оригинала) | число (+ толще / − тоньше) | 0 (как есть);
  lx_R       — сколько пикселей снаружи переносить (24); lx_dmax — глубина внутрь (по оригиналу);
  lx_nv      — число полос по высоте (16); lx_nd — секторов направления (8; 1 — без направления);
  lx_stripe  — (угол°, период) косых полос; lx_rot — угол наклона строк оригинала (для v);
  lx_bg      — цвет фона (DXT1 с чёрным фоном), иначе прозрачный; lx_ss — сверхвыборка (2);
  pixel=k    — пиксель-арт: всё в разрешении 1/k (фаза сетки определяется сама), увеличение без сглаживания;
  lx_keep    — прямоугольники (x0,y0,x1,y1) из оригинала как есть (картинки рядом с текстом);
  lx_post    — функция (orig, spec, img) -> img для доводки."""
import numpy as np
import cv2
from PIL import Image
from scipy.spatial import cKDTree


def shape_mask(a, thr=128, lum=False, lum_thr=None, sel=None):
    """Маска «тела» букв оригинала. sel: None/'alpha' — по альфе; 'bright' — альфа и яркость > lum_thr
    (светлая заливка внутри тёмной обводки); 'dark' — альфа и яркость < lum_thr (тёмные буквы со свечением);
    lum=True — только по яркости (DXT1 без альфы)."""
    L = a[:, :, :3].max(2)
    if lum:
        return L > (lum_thr if lum_thr is not None else thr)
    al = a[:, :, 3] > thr
    if sel == 'bright':
        return al & (L > (lum_thr if lum_thr is not None else 128))
    if sel == 'dark':
        return al & (L < (lum_thr if lum_thr is not None else 100))
    if sel == 'clear':
        return a[:, :, 3] < thr
    if sel == 'sat':
        # цветная заливка (насыщенная), без белых ободков и тёмных обводок; полосы внутри — закрытием
        A = a[:, :, :3].astype(np.float32)
        mx = A.max(2); mn = A.min(2)
        S = (mx - mn) / np.maximum(mx, 1)
        m = al & (S > 0.32) & (mx > 70)
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
        # заполнить небольшие дырки
        inv = (~m).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
        for i in range(1, n):
            if st[i, 4] < 12 and st[i, 0] > 0 and st[i, 1] > 0:
                m[lab == i] = True
        return m
    if isinstance(sel, tuple) and sel[0] == 'erode':
        # «сердцевина» надписи: маска, суженная на sel[1] пикселей (обводки/ободки — снаружи от неё)
        d = cv2.distanceTransform(al.astype(np.uint8), cv2.DIST_L2, 5)
        return d > sel[1]
    return al


def letter_height(m):
    b = bands_of(m)
    return max((e - s for s, e in b), default=0)


def signed_dist(m):
    m8 = m.astype(np.uint8)
    din = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    dout = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 5)
    return np.where(m, din - 0.5, -dout + 0.5).astype(np.float32)


def angle_of(sd):
    g = cv2.GaussianBlur(sd, (0, 0), 2.0)
    gy, gx = np.gradient(g)
    return np.mod(np.arctan2(-gy, -gx), 2 * np.pi)      # направление наружу


def half_width(m):
    m8 = m.astype(np.uint8)
    d = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    mx = cv2.dilate(d, np.ones((3, 3), np.uint8))
    ridge = (d >= mx - 1e-3) & (d > 0.8)
    v = d[ridge]
    if not len(v):
        return 0.0
    v = v[v >= 0.3 * v.max()]          # тонкие кольца/хвосты не учитываем
    return float(np.median(v))


def match_width(m, target):
    delta = target - half_width(m)
    if abs(delta) < 0.35:
        return m
    m8 = m.astype(np.uint8)
    if delta > 0:
        return m | (cv2.distanceTransform(1 - m8, cv2.DIST_L2, 5) <= delta)
    return m & (cv2.distanceTransform(m8, cv2.DIST_L2, 5) > -delta)


def bands_of(m, gap=2):
    rows = m.any(1)
    out = []; y = 0; H = len(rows)
    while y < H:
        if rows[y]:
            s = y
            while y < H and rows[y]: y += 1
            if out and s - out[-1][1] <= gap:
                out[-1][1] = y
            else:
                out.append([s, y])
        y += 1
    return out


def vmap(m, rot=0.0):
    """Высота точки внутри своей строки (0 — верх строки, 1 — низ). rot — наклон строк (градусы, как в PIL.rotate)."""
    H, W = m.shape
    if rot:
        M = cv2.getRotationMatrix2D((W / 2, H / 2), -rot, 1.0)
        ms = cv2.warpAffine(m.astype(np.uint8), M, (W, H), flags=cv2.INTER_NEAREST) > 0
        vs = vmap(ms)
        Mi = cv2.getRotationMatrix2D((W / 2, H / 2), rot, 1.0)
        return cv2.warpAffine(vs, Mi, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    bands = bands_of(m)
    v = np.zeros((H, W), np.float32)
    if not bands:
        return v
    col = np.zeros(H, np.float32)
    for y in range(H):
        b = min(bands, key=lambda b: 0 if b[0] <= y < b[1] else min(abs(y - b[0]), abs(y - (b[1] - 1))))
        col[y] = (y - b[0]) / max(1.0, b[1] - b[0] - 1)
    v[:] = col[:, None]
    return v


def stripe_phase(H, W, stripe):
    if not stripe:
        return None
    ang, per = stripe
    t = np.deg2rad(ang)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return ((xx * np.cos(t) + yy * np.sin(t)) / per) % 1.0


class LUT:
    def __init__(self, img, m, R=24, dmax=None, nv=16, nd=8, stripe=None, nph=4, vclip=(-0.6, 1.6), rot=0.0):
        a = img.astype(np.float32)
        H, W = m.shape
        sd = signed_dist(m)
        self.R = R
        self.dmax = dmax if dmax is not None else max(2.0, float(np.percentile(sd[m], 99.5)) if m.any() else 2.0)
        self.nv = nv; self.nd = max(1, nd); self.vclip = vclip; self.stripe = stripe; self.nph = nph if stripe else 1
        v = vmap(m, rot)
        ang = angle_of(sd)
        ph = stripe_phase(H, W, stripe)
        sel = (sd > -R) & (sd < self.dmax + 1)
        self.ND = int(np.ceil(R + self.dmax)) + 1
        di = np.clip(np.round(sd[sel] + R).astype(np.int32), 0, self.ND - 1)
        lo, hi = vclip
        vi = np.clip(((v[sel] - lo) / (hi - lo) * nv).astype(np.int32), 0, nv - 1)
        step = 2 * np.pi / self.nd
        ri = (np.round(ang[sel] / step).astype(np.int32) % self.nd)
        pi = (np.floor(ph[sel] * self.nph).astype(np.int32) % self.nph) if ph is not None else np.zeros(sel.sum(), np.int32)
        shape = (self.ND, nv, self.nd, self.nph)
        col = a[sel]
        pm = col.copy(); pm[:, :3] *= pm[:, 3:4] / 255.0
        key = ((di * nv + vi) * self.nd + ri) * self.nph + pi
        n = int(np.prod(shape))
        cnt = np.bincount(key, minlength=n)
        tab = np.zeros((n, 4), np.float32)
        order = np.argsort(key, kind='stable')
        ks = key[order]; cs = pm[order]
        bounds = np.searchsorted(ks, np.arange(n + 1))
        for k in np.where(cnt > 0)[0]:
            tab[k] = np.median(cs[bounds[k]:bounds[k + 1]], axis=0)
        filled = np.where(cnt > 0)[0]
        if len(filled) and len(filled) < n:
            coords = np.stack(np.unravel_index(np.arange(n), shape), -1).astype(np.float32)
            wts = np.array([1.0, 0.7, 0.3, 0.2], np.float32)
            ext = []; idx = []
            for sh in (0, -self.nd, self.nd):          # направление — по кругу
                c2 = coords[filled].copy(); c2[:, 2] += sh; ext.append(c2 * wts); idx.append(filled)
            tree = cKDTree(np.vstack(ext)); allidx = np.concatenate(idx)
            empty = np.where(cnt == 0)[0]
            _, j = tree.query(coords[empty] * wts, k=1)
            tab[empty] = tab[allidx[j]]
        self.tab = tab.reshape(shape + (4,))

    def render(self, m, rot=0.0, far=None, nearest=False):
        H, W = m.shape
        sd = signed_dist(m)
        if nearest:
            return self.render_nearest(m, sd, rot, far)
        v = vmap(m, rot)
        ang = angle_of(sd)
        ph = stripe_phase(H, W, self.stripe)
        sel = sd > -self.R
        fd = np.clip(sd[sel] + self.R, 0, self.ND - 1)
        d0 = np.floor(fd).astype(np.int32); d1 = np.minimum(d0 + 1, self.ND - 1); td = (fd - d0)[:, None]
        lo, hi = self.vclip
        fv = np.clip((v[sel] - lo) / (hi - lo) * self.nv - 0.5, 0, self.nv - 1)
        v0 = np.floor(fv).astype(np.int32); v1 = np.minimum(v0 + 1, self.nv - 1); tv = (fv - v0)[:, None]
        fa = ang[sel] / (2 * np.pi / self.nd)
        a0 = np.floor(fa).astype(np.int32) % self.nd; a1 = (a0 + 1) % self.nd; ta = (fa - np.floor(fa))[:, None]
        if self.nd == 1:
            ta = ta * 0
        pi = (np.floor(ph[sel] * self.nph).astype(np.int32) % self.nph) if ph is not None else np.zeros(sel.sum(), np.int32)
        T = self.tab
        c = 0
        for dd, wd in ((d0, 1 - td), (d1, td)):
            for vv, wv in ((v0, 1 - tv), (v1, tv)):
                for aa, wa in ((a0, 1 - ta), (a1, ta)):
                    c = c + T[dd, vv, aa, pi] * (wd * wv * wa)
        out = np.zeros((H, W, 4), np.float32)
        if far is not None:
            # дальше R от букв — сплошной цвет (например, чёрная плашка трафарета)
            f = np.array(far, np.float32); f[:3] *= f[3] / 255.0
            out[:] = f
        out[sel] = c
        return out          # премультиплицированный float

    def render_nearest(self, m, sd, rot, far):
        """Пиксель-арт: без интерполяции (кольца по 1 пикселю не смешиваются)."""
        H, W = m.shape
        v = vmap(m, rot)
        ang = angle_of(sd)
        ph = stripe_phase(H, W, self.stripe)
        sel = sd > -self.R
        di = np.clip(np.round(sd[sel] + self.R).astype(np.int32), 0, self.ND - 1)
        lo, hi = self.vclip
        vi = np.clip(((v[sel] - lo) / (hi - lo) * self.nv).astype(np.int32), 0, self.nv - 1)
        ri = (np.round(ang[sel] / (2 * np.pi / self.nd)).astype(np.int32) % self.nd)
        pi = (np.floor(ph[sel] * self.nph).astype(np.int32) % self.nph) if ph is not None else np.zeros(sel.sum(), np.int32)
        out = np.zeros((H, W, 4), np.float32)
        if far is not None:
            f = np.array(far, np.float32); f[:3] *= f[3] / 255.0
            out[:] = f
        out[sel] = self.tab[di, vi, ri, pi]
        return out


def unpremul(out):
    al = out[:, :, 3:4]
    rgb = np.where(al > 0.5, out[:, :, :3] * 255.0 / np.clip(al, 1e-3, 255), 0)
    return np.clip(np.concatenate([rgb, al], 2), 0, 255).astype(np.uint8)


def grid_phase(a, k):
    """Фаза сетки пиксель-арта по x и по y: остаток по модулю k, на котором чаще всего меняется цвет."""
    A = a.astype(np.int32)
    dx = np.any(np.abs(np.diff(A, axis=1)) > 30, axis=2)
    dy = np.any(np.abs(np.diff(A, axis=0)) > 30, axis=2)
    hx = np.bincount((np.where(dx)[1] + 1) % k, minlength=k)
    hy = np.bincount((np.where(dy)[0] + 1) % k, minlength=k)
    return int(np.argmax(hx)), int(np.argmax(hy))


def text_mask(spec, om):
    """Маска новой надписи (uint8 0..255) по раскладке spec — как обычная надпись в texedit.apply_spec
    (поля, выравнивание, grow, fit считаются по маске оригинала om)."""
    import texedit
    H, W = om.shape
    ref = np.zeros((H, W, 4), np.uint8); ref[..., :3] = 255; ref[..., 3] = om.astype(np.uint8) * 255
    ref = Image.fromarray(ref)
    s2 = dict(spec)
    for key in ('custom', 'gradient', 'glow', 'shadow', 'strokes', 'stroke', 'under', 'keep_dots', 'halftone', 'first_fill',
                'hollow', 'hollow_inner', 'embolden', 'bg', 'basefill', 'keep_boxes'):
        s2.pop(key, None)
    s2['fill'] = (255, 255, 255, 255); s2['clear'] = 'all'
    if s2.get('lx_layout'):
        lay = s2['lx_layout'](ref, s2)
    elif s2.get('layers'):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        for L in s2['layers']:
            sub = dict(L)
            for key in ('gradient', 'glow', 'shadow', 'strokes', 'stroke'):
                sub.pop(key, None)
            sub['fill'] = (255, 255, 255, 255)
            l1 = texedit.fit_layer(ref, sub, (W, H), sub['box'])
            if sub.get('rotate'):
                b = sub['box']; l1 = l1.rotate(sub['rotate'], resample=Image.BICUBIC, center=((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
            lay = Image.alpha_composite(lay, l1)
    else:
        lay = texedit.apply_spec(ref, s2)
    if s2.get('rot_all'):
        # поворот всей надписи (несколько строк) вокруг общего центра
        lay = lay.rotate(s2['rot_all'], resample=Image.BICUBIC, center=s2.get('rot_center', (W / 2, H / 2)))
    return np.asarray(lay)[:, :, 3]


def scale_spec(spec, f):
    s = dict(spec)
    def sc(v):
        if isinstance(v, (tuple, list)): return tuple(x * f for x in v)
        return v * f
    for key in ('box', 'textbox', 'cap', 'base_y', 'cap_y', 'maxw', 'clearbox', 'tracking', 'dx', 'dy', 'fit_maxdy', 'vband', 'r0', 'center', 'rot_center'):
        if s.get(key) is not None:
            s[key] = sc(s[key])
    if s.get('layers'):
        s['layers'] = [dict(L, **{kk: sc(L[kk]) for kk in ('box', 'cap', 'maxw', 'tracking', 'dx', 'dy') if L.get(kk) is not None}) for L in s['layers']]
    return s


def lut_custom(orig, spec):
    W, H = orig.size
    k = spec.get('pixel', 1)
    ss = 1 if k > 1 else spec.get('lx_ss', 2)
    a = np.asarray(orig.convert('RGBA'))
    ox = oy = 0
    if k > 1:
        ph = spec.get('pixel_phase') or grid_phase(a, k)
        ox = (ph[0] + k // 2) % k; oy = (ph[1] + k // 2) % k
        a = a[oy::k, ox::k]
        f = 1.0 / k
    else:
        if ss > 1:
            a = np.asarray(Image.fromarray(a).resize((W * ss, H * ss), Image.BICUBIC))
        f = float(ss)
    h, w = a.shape[:2]
    sel_ = spec.get('lx_sel')
    er = spec.get('lx_erode', 0) * (ss if k == 1 else 1.0)
    om = shape_mask(a, spec.get('lx_thr', 128), spec.get('lx_lum', False), spec.get('lx_lum_thr'), sel_)
    om_full = om
    if sel_ == 'sat':
        er = 0
    if er:
        # таблица строится от «сердцевины» (маска, суженная на er): обводки и ободки — кольца снаружи неё;
        # новая надпись раскладывается по полной маске и сужается на столько же
        om = cv2.distanceTransform(om_full.astype(np.uint8), cv2.DIST_L2, 5) > er
    if spec.get('lx_open'):
        # убрать тонкие кольца обводки/хвосты/шум маски (размер — в пикселях текстуры)
        kk = 3 if spec['lx_open'] is True else spec['lx_open']
        kk = max(3, int(round(kk * (ss if k == 1 else 1.0 / k)))) | 1
        om = cv2.morphologyEx(om.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk))) > 0
    if spec.get('lx_close'):
        # заполнить царапины/дырки внутри букв (гранж)
        kk = int(spec['lx_close'] * (ss if k == 1 else 1.0 / k)) | 1
        om = cv2.morphologyEx(om.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk))) > 0
    for kb in spec.get('lx_keep') or []:
        x0, y0, x1, y1 = [int(round(v * f)) for v in kb]
        om[y0:y1, x0:x1] = False
    rot = spec.get('lx_rot', 0)
    R = spec.get('lx_R', 24) * f
    dmax = spec.get('lx_dmax'); dmax = dmax * f if dmax else None
    lut = LUT(a, om, R=R, dmax=dmax, nv=spec.get('lx_nv', 16), nd=spec.get('lx_nd', 8),
              stripe=spec.get('lx_stripe'), vclip=spec.get('lx_vclip', (-0.6, 1.6)), rot=rot)
    s = scale_spec(spec, f)
    core_layout = er and spec.get('lx_core_layout', True)
    nmask = text_mask(s, om if core_layout else om_full)
    nm = nmask > spec.get('lx_mthr', 110)
    core = spec.get('lx_core', 'auto')
    if er and not core_layout:
        if core == 'auto':
            ho, hn = letter_height(om_full), letter_height(nm)
            nm = match_width(nm, half_width(om_full) * (hn / ho if ho and hn else 1.0) * spec.get('lx_wk', 1.0))
        elif core:
            nm = match_width(nm, half_width(nm) + core * f)
        nm = cv2.distanceTransform(nm.astype(np.uint8), cv2.DIST_L2, 5) > er
        core = 0
    if core == 'auto':
        # толщина штриха — пропорционально высоте букв (как у оригинала), с коэффициентом lx_wk
        rot = spec.get('lx_rot', 0)
        def lh(m):
            if rot:
                M = cv2.getRotationMatrix2D((m.shape[1] / 2, m.shape[0] / 2), -rot, 1.0)
                m = cv2.warpAffine(m.astype(np.uint8), M, (m.shape[1], m.shape[0]), flags=cv2.INTER_NEAREST) > 0
            return letter_height(m)
        ho, hn = lh(om), lh(nm)
        tgt = half_width(om) * (hn / ho if ho and hn else 1.0) * spec.get('lx_wk', 1.0)
        nm = match_width(nm, tgt)
    elif core:
        nm = match_width(nm, half_width(nm) + core * f)
    out = lut.render(nm, rot=spec.get('lx_rot_new', rot), far=spec.get('lx_far'), nearest=spec.get('lx_nearest', k > 1))
    if k > 1:
        img = Image.fromarray(unpremul(out))
        big = img.resize((w * k, h * k), Image.NEAREST)
        full = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        full.paste(big, (ox - k // 2, oy - k // 2))
        img = full
    elif ss > 1:
        small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
        img = Image.fromarray(unpremul(small))
    else:
        img = Image.fromarray(unpremul(out))
    bg = spec.get('lx_bg')
    if bg is not None:
        img = Image.alpha_composite(Image.new('RGBA', (W, H), tuple(bg)), img)
    for kb in spec.get('lx_keep') or []:
        img.paste(orig.crop(kb), (kb[0], kb[1]))
    if spec.get('lx_post'):
        img = spec['lx_post'](orig, spec, img)
    return img
