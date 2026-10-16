"""Особые надписи v2.4 (custom-функции для tex_specs).

splatter_under(orig, spec)  — подложка: брызги/царапины оригинала вдали от старых букв (для гранж-надписей COMBO).
cutin_custom(orig, spec)    — кат-ин «Miss»: старые буквы вырезаются (лучи остаются), новые рисуются по LUT старых.
zoomblur_custom(orig, spec) — «эффектная» копия надписи (радиальное размытие, DXT1 на чёрном фоне):
                              строится из маски новой надписи; цвета подбираются по оригиналу.
pair_mask(spec)             — маска новой надписи для парной текстуры (чтобы эффект совпадал с основной)."""
import numpy as np
import cv2
from PIL import Image


def _core(a, thr_a=200, thr_l=200, close=5):
    al = a[:, :, 3]; L = a[:, :, :3].max(2)
    core = (al > thr_a) & (L > thr_l)
    if close:
        core = cv2.morphologyEx(core.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((close, close), np.uint8)) > 0
    return core


def splatter_under(orig, spec):
    a = np.array(orig.convert('RGBA'))
    core = _core(a, spec.get('splat_thr_a', 200), spec.get('splat_thr_l', 200), spec.get('splat_close', 5))
    gap = spec.get('splat_gap', 6)
    far = cv2.distanceTransform((1 - core).astype(np.uint8), cv2.DIST_L2, 5) > gap
    out = a.copy()
    out[~far, 3] = 0
    # слабые (почти прозрачные) остатки свечения тоже убираем
    out[:, :, 3] = np.where(out[:, :, 3] < spec.get('splat_min_a', 40), 0, out[:, :, 3])
    return Image.fromarray(out)


def letters_mask(a, dark_thr=60, alpha_thr=200, r=9):
    """Толстые чёрные буквы без тонких лучей: раскрытие диском r, затем восстановление внутри исходной маски."""
    m = (a[:, :, 3] > alpha_thr) & (a[:, :, :3].max(2) < dark_thr)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    seed = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k)
    # геодезическое восстановление (ограниченное: несколько шагов, чтобы не утечь по лучам далеко)
    rec = seed.copy()
    k3 = np.ones((3, 3), np.uint8)
    for _ in range(r + 2):
        rec = cv2.dilate(rec, k3) & m.astype(np.uint8)
    return rec > 0


def cutin_new_letters(orig, spec, ss=2):
    """Маска новых букв кат-ина (в масштабе ss) и маска старых букв (там же)."""
    import lutfx
    W, H = orig.size
    a = np.array(orig.convert('RGBA'))
    lm = letters_mask(a, spec.get('ci_dark', 60), 200, spec.get('ci_r', 9))
    lm2 = cv2.resize(lm.astype(np.uint8), (W * ss, H * ss), interpolation=cv2.INTER_NEAREST) > 0
    s = lutfx.scale_spec(spec, ss)
    nm = lutfx.text_mask(s, lm2) > 110
    nm = lutfx.match_width(nm, lutfx.half_width(lm2) * spec.get('lx_wk', 1.0))
    return nm, lm2


def cutin_custom(orig, spec):
    import lutfx
    W, H = orig.size
    a = np.array(orig.convert('RGBA'))
    lm = letters_mask(a, spec.get('ci_dark', 60), 200, spec.get('ci_r', 9))
    # стереть старые буквы вместе с ободком и свечением
    dist = cv2.distanceTransform((1 - lm).astype(np.uint8), cv2.DIST_L2, 5)
    erase = dist <= spec.get('ci_erase', 14)
    base = a.copy(); base[erase, 3] = 0
    # мягкая тень старых букв (полупрозрачная) — убрать и дальше, лучи (непрозрачные) оставить
    zone = (dist <= spec.get('ci_shadow', 26)) & (base[:, :, 3] < spec.get('ci_shadow_a', 200))
    base[zone, 3] = 0
    # таблица оформления по старым буквам (только их окрестность)
    ss = spec.get('lx_ss', 2)
    A2 = np.asarray(Image.fromarray(a).resize((W * ss, H * ss), Image.BICUBIC))
    lm2 = cv2.resize(lm.astype(np.uint8), (W * ss, H * ss), interpolation=cv2.INTER_NEAREST) > 0
    near = cv2.distanceTransform((1 - lm2).astype(np.uint8), cv2.DIST_L2, 5) <= spec.get('ci_erase', 14) * ss
    A2m = A2.copy(); A2m[~near, 3] = 0          # лучи вдали не учитываем
    lut = lutfx.LUT(A2m, lm2, R=spec.get('lx_R', 12) * ss, nv=spec.get('lx_nv', 12), nd=spec.get('lx_nd', 8))
    nm, _ = cutin_new_letters(orig, spec, ss)
    out = lut.render(nm)
    small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
    new = Image.fromarray(lutfx.unpremul(small))
    res = Image.alpha_composite(Image.fromarray(base), new)
    return res


def pair_mask(spec, size):
    """Маска новой надписи (float 0..1) так, как её рисует парная текстура spec['zb_pair'] (тот же spec раскладки)."""
    import texedit, lutfx
    W, H = size
    spc = texedit.load_arch(spec['arch'])
    E = {e.name: e for e in spc['entries']}
    from srdtex import textures, decode
    po = None
    for n in E:
        if n.endswith('.srd') and n + 'v' in E and (not spec.get('srd') or spec['srd'] == n):
            for t in textures(E[n].data):
                if t['name'] == spec['zb_pair']:
                    po = decode(t, E[n + 'v'].data)
    assert po is not None, spec['zb_pair']
    ps = dict(spec['zb_pair_spec']); ps['arch'] = spec['arch']
    img = ps['custom'](po, ps)
    a = np.asarray(img).astype(np.float32)
    return a[:, :, 3] / 255.0 * (a[:, :, :3].max(2) / 255.0 if spec.get('zb_lum') else 1.0), po


def zoom_blur(m, center, strength=1.0, steps=96, gauss=3, hblur=0, decay=1.5):
    """Радиальное (zoom) размытие с затуханием — длинные лучи от букв, как у кат-ина оригинала."""
    H, W = m.shape
    cx, cy = center
    acc = np.zeros_like(m, np.float32); ws = 0.0
    for i in range(steps):
        t = i / (steps - 1)
        s = 1.0 + strength * t
        w = (1 - t) ** decay + 0.02
        M = np.float32([[s, 0, cx - s * cx], [0, s, cy - s * cy]])
        acc += w * cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR); ws += w
    acc /= ws
    if gauss:
        acc = cv2.GaussianBlur(acc, (0, 0), gauss)
    if hblur and hblur > 1:
        acc = cv2.blur(acc, (hblur, 1))
    return acc


def zoomblur_custom(orig, spec):
    """Эффектная копия: радиальное размытие новой надписи; цвет — по таблице «яркость размытия → цвет», снятой с оригинала."""
    W, H = orig.size
    a = np.asarray(orig.convert('RGBA')).astype(np.float32)
    if spec.get('zb_cutin'):
        # буквы кат-ина (без лучей): новые — по раскладке парной текстуры, старые — из её оригинала
        import texedit
        from srdtex import textures, decode
        spc = texedit.load_arch(spec['arch']); E = {e.name: e for e in spc['entries']}
        po = None
        for n in E:
            if n.endswith('.srd') and n + 'v' in E and (not spec.get('srd') or spec['srd'] == n):
                for t in textures(E[n].data):
                    if t['name'] == spec['zb_pair']: po = decode(t, E[n + 'v'].data)
        nm2, lm2 = cutin_new_letters(po, dict(spec['zb_pair_spec'], arch=spec['arch']), 2)
        new_m = cv2.resize(nm2.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)
        old_m = cv2.resize(lm2.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)
    else:
        new_m, po = pair_mask(spec, (W, H))
        pa = np.asarray(po.convert('RGBA')).astype(np.float32)
        old_m = (pa[:, :, 3] / 255.0) * (1.0 if not spec.get('zb_old_dark') else (pa[:, :, :3].max(2) < 80))
    ys, xs = np.where(old_m > 0.5)
    c = spec.get('zb_center', (float(xs.mean()), float(ys.mean())) if len(xs) else (W / 2, H / 2)); st = spec.get('zb_strength', 0.4)
    old_b = zoom_blur(old_m.astype(np.float32), c, st)
    new_b = zoom_blur(new_m.astype(np.float32), c, st)
    # таблица: значение размытия -> медианный цвет оригинала
    bins = 32
    vo = np.clip((old_b / max(1e-6, old_b.max()) * (bins - 1)).astype(int), 0, bins - 1)
    tab = np.zeros((bins, 4), np.float32); have = np.zeros(bins, bool)
    for b in range(bins):
        sel = vo == b
        if sel.sum() > 20:
            tab[b] = np.median(a[sel], 0); have[b] = True
    idx = np.where(have)[0]
    for b in range(bins):
        if not have[b]:
            tab[b] = tab[idx[np.argmin(np.abs(idx - b))]]
    vn = np.clip((new_b / max(1e-6, old_b.max()) * (bins - 1)), 0, bins - 1)
    v0 = np.floor(vn).astype(int); v1 = np.minimum(v0 + 1, bins - 1); t = (vn - v0)[..., None]
    out = tab[v0] * (1 - t) + tab[v1] * t
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def copy_tex(orig, spec):
    """Копия другой текстуры того же файла (spec['copy_from'], в том же srd, если задан spec['srd']), если размеры совпадают."""
    import texedit
    from srdtex import textures, decode
    spc = texedit.load_arch(spec['arch'])
    E = {e.name: e for e in spc['entries']}
    for n in E:
        if n.endswith('.srd') and n + 'v' in E and (not spec.get('srd') or spec['srd'] == n):
            for t in textures(E[n].data):
                if t['name'] == spec['copy_from']:
                    im = decode(t, E[n + 'v'].data)
                    assert im.size == orig.size, (im.size, orig.size)
                    return im
    raise KeyError(spec['copy_from'])


def scratch_post(orig, spec, img):
    """Перенести «царапины» оригинала: внутри старых букв — отношение яркости к цвету заливки; затемняем новые буквы там же."""
    a = np.asarray(orig.convert('RGBA')).astype(np.float32)
    n = np.asarray(img.convert('RGBA')).astype(np.float32)
    core = _core(a.astype(np.uint8), 200, 120, 5)
    L = a[:, :, :3].max(2)
    fillL = np.median(L[core & (a[:, :, 3] > 200)]) if core.any() else 255
    ratio = np.ones(L.shape, np.float32)
    inside = core
    ratio[inside] = np.clip((L[inside] + (255 - a[inside][:, 3])) / max(1, fillL), 0.25, 1.0)
    k = spec.get('scr_k', 1.0)
    ratio = 1 - (1 - ratio) * k
    out = n.copy()
    out[:, :, :3] *= ratio[:, :, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def glitch_custom(orig, spec):
    """Надпись с «глитчем» (Беззаконный пробег): белые буквы, циановая и пурпурная копии со сдвигом, косые царапины.
    spec: text/font/box/... (раскладка как обычно), gl_shift=(dx,dy), gl_bg — фон (для DXT1 — чёрный), gl_scratch — число царапин."""
    import texedit
    W, H = orig.size
    a = np.asarray(orig.convert('RGBA'))
    if spec.get('gl_lum', True):
        om = a[:, :, :3].max(2) > 150
    else:
        om = a[:, :, 3] > 128
    ref = np.zeros((H, W, 4), np.uint8); ref[..., :3] = 255; ref[..., 3] = om * 255
    s2 = {k: v for k, v in spec.items() if k not in ('custom', 'glow', 'strokes', 'stroke', 'shadow', 'gradient')}
    s2['fill'] = (255, 255, 255, 255); s2['clear'] = 'all'
    lay = texedit.apply_spec(Image.fromarray(ref), s2)
    m = np.asarray(lay)[:, :, 3].astype(np.float32) / 255
    dx, dy = spec.get('gl_shift', (6, 3))
    def sh(x, ox, oy):
        M = np.float32([[1, 0, ox], [0, 1, oy]])
        return cv2.warpAffine(x, M, (W, H), flags=cv2.INTER_LINEAR)
    cy_ = sh(m, -dx, dy); mg = sh(m, dx, -dy)
    # косые царапины (короткие отрезки ~70°) — случайно, но воспроизводимо
    rng = np.random.default_rng(spec.get('seed', 7))
    ys, xs = np.where(m > 0.5)
    scr = np.zeros((H, W), np.uint8)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        for _ in range(spec.get('gl_scratch', 40)):
            # царапины — только у букв: начало внутри буквы
            j = rng.integers(len(xs)); x = xs[j] + rng.uniform(-6, 6); y = ys[j] + rng.uniform(-6, 6)
            L = rng.uniform(0.1, 0.35) * (y1 - y0)
            ang = np.deg2rad(rng.uniform(62, 78))
            p0 = (int(x), int(y)); p1 = (int(x + L * np.cos(ang)), int(y + L * np.sin(ang)))
            cv2.line(scr, p0, p1, 255, max(1, int(rng.uniform(1, 2.6))), cv2.LINE_AA)
    sc = scr.astype(np.float32) / 255
    out = np.zeros((H, W, 3), np.float32)
    bg = spec.get('gl_bg')
    # цветные копии (аддитивно), белые буквы и царапины поверх
    out += cy_[..., None] * np.array([0, 170, 255], np.float32)
    out += mg[..., None] * np.array([255, 20, 190], np.float32)
    out = np.clip(out, 0, 255)
    white = np.clip(m + sc * 0.9, 0, 1)
    out = out * (1 - white[..., None]) + 255 * white[..., None]
    # цветные края царапин
    out += sh(sc, -2, 1)[..., None] * np.array([0, 120, 200], np.float32) * 0.6
    out = np.clip(out, 0, 255)
    alpha = np.clip(np.maximum.reduce([m, cy_, mg, sc]), 0, 1) * 255
    if bg is not None:
        res = np.concatenate([out, np.full((H, W, 1), 255, np.float32)], 2)
        res[..., :3] = res[..., :3] * (alpha[..., None] / 255) + np.array(bg[:3], np.float32) * (1 - alpha[..., None] / 255)
    else:
        res = np.concatenate([out, alpha[..., None]], 2)
    return Image.fromarray(res.astype(np.uint8))


def zoomfx_custom(orig, spec):
    """Эффектная копия «глитч»-надписи: радиальное размытие парной (новой) текстуры.
    Параметры размытия подобраны по оригиналу (корреляция 0.97): центр — центр текстуры, сила 0.1–0.2, затухание 2, сглаживание 3.
    Яркость/альфа: линейная подгонка «размытый оригинал → эффект оригинала», та же применяется к новой надписи."""
    import texedit
    from srdtex import textures, decode
    W, H = orig.size
    spc = texedit.load_arch(spec['arch']); E = {e.name: e for e in spc['entries']}
    po = None
    for n in E:
        if n.endswith('.srd') and n + 'v' in E and (not spec.get('srd') or spec['srd'] == n):
            for t in textures(E[n].data):
                if t['name'] == spec['zb_pair']: po = decode(t, E[n + 'v'].data)
    ps = dict(spec['zb_pair_spec'], arch=spec['arch'])
    new = np.asarray(ps['custom'](po, ps)).astype(np.float32) / 255
    old = np.asarray(po.convert('RGBA')).astype(np.float32) / 255
    a = np.asarray(orig.convert('RGBA')).astype(np.float32) / 255
    c = spec.get('zb_center', (W / 2, H / 2))
    kw = dict(strength=spec.get('zb_strength', 0.1), steps=48, gauss=spec.get('zb_gauss', 3), hblur=0, decay=spec.get('zb_decay', 2.0))
    bo = np.stack([zoom_blur(old[:, :, ch], c, **kw) for ch in range(3)], -1)
    bn = np.stack([zoom_blur(new[:, :, ch], c, **kw) for ch in range(3)], -1)
    tgt = a[:, :, 3] if spec.get('zb_alpha') else a[:, :, :3].max(2)
    x = bo.max(2).ravel(); y = tgt.ravel()
    A = np.vstack([x, np.ones_like(x)]).T
    k, b0 = np.linalg.lstsq(A, y, rcond=None)[0]
    mx = bn.max(2)
    level = np.clip(k * mx + b0, 0, 1)
    if spec.get('zb_alpha'):
        rgb = np.where(mx[..., None] > 1e-4, bn / np.maximum(mx[..., None], 1e-4), 0)
        res = np.concatenate([rgb, level[..., None]], 2)
    else:
        rgb = np.where(mx[..., None] > 1e-4, bn / np.maximum(mx[..., None], 1e-4), 0) * level[..., None]
        res = np.concatenate([rgb, np.ones((H, W, 1), np.float32)], 2)
    return Image.fromarray(np.clip(res * 255, 0, 255).astype(np.uint8))


def rotstyle_custom(orig, spec):
    """Повёрнутая надпись, у которой заливка-градиент идёт по вертикали экрана (как у «DAY» по диагонали):
    маска раскладывается обычным образом (с rotate), оформление (strokes, gradient) — уже после поворота."""
    import texedit, lutfx
    W, H = orig.size
    om = np.asarray(orig.convert('RGBA'))[:, :, 3] > 128
    s2 = dict(spec); s2.pop('custom', None)
    nm = lutfx.text_mask(s2, om)
    s3 = dict(spec); s3.pop('rotate', None); s3.pop('custom', None)
    if s3.get('gradient') == 'orig':
        s3['gradient'] = texedit.orig_gradient(orig, s3.get('grad_box'), s3.get('grad_erode', 3), s3.get('grad_bins', 12), s3.get('grad_lum'))
    lay = texedit.style(Image.fromarray(nm), s3, (W, H))
    return Image.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 0)), lay)


def _seg_dist(X, Y, p0, p1):
    """Расстояние от точек до отрезка p0-p1 и параметр проекции s (0..1)."""
    x0, y0 = p0; x1, y1 = p1
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy or 1.0
    s = ((X - x0) * vx + (Y - y0) * vy) / L2
    sc = np.clip(s, 0, 1)
    dx = X - (x0 + sc * vx); dy = Y - (y0 + sc * vy)
    return np.sqrt(dx * dx + dy * dy), s


def n2h_custom(orig, spec):
    """Неоновая N -> Н (MONOMONO на автомате Мономоно): диагональ убирается (фон восстанавливается inpaint),
    между серединами ножек — перекладина того же профиля трубки, что и у ножек.
    spec['n2h'] = [dict(L=((x,y),(x,y)), R=((x,y),(x,y)), D=((x,y),(x,y)), box=(x0,y0,x1,y1), w=7)],
    spec['n2h_mask'] = 'cyan' | ('lum', порог) — какие точки считаются трубкой со свечением."""
    a = np.asarray(orig.convert('RGBA')).astype(np.float32)
    H, W = a.shape[:2]
    out = a.copy()
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    for L in spec['n2h']:
        x0, y0, x1, y1 = L['box']
        sub = a[y0:y1, x0:x1].copy()
        Xs, Ys = X[y0:y1, x0:x1], Y[y0:y1, x0:x1]
        r, g, b = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
        mk = spec.get('n2h_mask', 'cyan')
        if mk == 'cyan':
            m = (b > 140) & (g > 140) & (r < 130)
        else:
            m = sub[:, :, :3].max(2) > mk[1]
        # уточнить оси ножек по ярким точкам (PCA): заданные концы — только примерные
        core = sub[:, :, :3].max(2) > np.percentile(sub[:, :, :3].max(2), 97) * 0.85
        L = dict(L)
        segd = {k: _seg_dist(Xs, Ys, *L[k])[0] for k in ('L', 'R', 'D')}
        for k in ('L', 'R'):
            others = np.minimum(*[segd[o] for o in ('L', 'R', 'D') if o != k])
            pm = core & (segd[k] < L.get('w', 7)) & (segd[k] < others - 1)
            if pm.sum() > 20:
                P = np.stack([Xs[pm], Ys[pm]], 1); mu = P.mean(0)
                u = np.linalg.svd(P - mu, full_matrices=False)[2][0]
                (ax, ay), (bx, by) = L[k]
                ta = (np.array([ax, ay]) - mu) @ u; tb = (np.array([bx, by]) - mu) @ u
                L[k] = (tuple(mu + ta * u), tuple(mu + tb * u))
        dN = np.minimum(np.minimum(_seg_dist(Xs, Ys, *L['L'])[0], _seg_dist(Xs, Ys, *L['R'])[0]), _seg_dist(Xs, Ys, *L['D'])[0])
        m &= dN < L.get('w', 7) * 0.5 + L.get('glow', 3) + 3
        m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=L.get('grow', 2))
        rgb = np.clip(sub[:, :, :3], 0, 255).astype(np.uint8)
        Bg = cv2.inpaint(np.ascontiguousarray(rgb[:, :, ::-1]), m, 5, cv2.INPAINT_TELEA)[:, :, ::-1].astype(np.float32)
        if mk != 'cyan':
            Bg = Bg * 0 + np.median(rgb[m == 0], 0) if (m == 0).any() else Bg * 0
        T = np.clip(sub[:, :, :3] - Bg, 0, None)
        # профиль трубки: поперёк обеих ножек (средняя часть), ось каждой уточняется по максимуму яркости
        w = L.get('w', 7)
        lum = T.mean(2)
        dds = []; vals = []; offs = {}
        for key in ('L', 'R'):
            (ax, ay), (bx, by) = L[key]
            vx, vy = bx - ax, by - ay; ln = np.hypot(vx, vy) or 1.0
            nx, ny = -vy / ln, vx / ln
            s_ = ((Xs - ax) * vx + (Ys - ay) * vy) / (ln * ln)
            d_ = (Xs - ax) * nx + (Ys - ay) * ny
            sel = (s_ > 0.2) & (s_ < 0.8) & (np.abs(d_) < w * 1.5)
            bins = np.round(d_[sel] * 2).astype(int)
            lv = lum[sel]
            ks = np.arange(bins.min(), bins.max() + 1)
            med = np.array([np.median(lv[bins == k]) if (bins == k).any() else 0 for k in ks])
            c = ks[np.argmax(np.convolve(med, np.ones(3) / 3, 'same'))] / 2.0
            offs[key] = c
            dds.append(np.abs(d_[sel] - c)); vals.append(T[sel])
        dd = np.concatenate(dds); vv = np.concatenate(vals)
        bins = np.round(dd * 2).astype(int)
        prof = np.zeros((bins.max() + 2, 3), np.float32)
        for k in range(len(prof)):
            v = vv[bins == k]
            if len(v): prof[k] = np.median(v, 0)
        c0 = offs['L']
        # только трубка и ближнее свечение: дальше — плавно в ноль (иначе ловится фон/соседние трубки)
        rmax = int(round((w * 0.5 + L.get('glow', 3)) * 2))
        prof = prof[:rmax + 1].copy()
        if len(prof) >= 3:
            prof[1:-1] = (prof[:-2] + 2 * prof[1:-1] + prof[2:]) / 4
        tail = min(6, len(prof))
        prof[-tail:] *= np.linspace(1, 0, tail)[:, None]
        pk = int(np.argmax(prof.mean(1)))
        for k in range(pk + 1, len(prof)):          # от оси наружу — только спад (без «колец» от соседних трубок)
            prof[k] = np.minimum(prof[k], prof[k - 1])
        def shift(seg):
            (p0x, p0y), (p1x, p1y) = seg
            ux, uy = p1x - p0x, p1y - p0y; l_ = np.hypot(ux, uy) or 1.0
            ox_, oy_ = -uy / l_ * c0, ux / l_ * c0
            return (p0x + ox_, p0y + oy_), (p1x + ox_, p1y + oy_)
        Ls = shift(L['L'])
        c0 = offs['R']; Rs = shift(L['R'])
        cA = ((Ls[0][0] + Ls[1][0]) / 2, (Ls[0][1] + Ls[1][1]) / 2)
        cB = ((Rs[0][0] + Rs[1][0]) / 2, (Rs[0][1] + Rs[1][1]) / 2)
        dmin = np.minimum(np.minimum(_seg_dist(Xs, Ys, *Ls)[0], _seg_dist(Xs, Ys, *Rs)[0]), _seg_dist(Xs, Ys, cA, cB)[0])
        fi = np.clip(dmin * 2, 0, len(prof) - 1)
        i0 = np.floor(fi).astype(int); i1 = np.minimum(i0 + 1, len(prof) - 1); t_ = (fi - i0)[:, :, None]
        Tn = prof[i0] * (1 - t_) + prof[i1] * t_
        out[y0:y1, x0:x1, :3] = np.clip(Bg + Tn, 0, 255)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def effect_custom(orig, spec):
    """Подписи эффектов RPG (Ice, Electric...): облако-подложка оригинала остаётся, старые буквы закрашиваются (inpaint),
    новые рисуются поверх обычным оформлением. spec['em_fill'] — цвет заливки букв (для масок, где обводка
    сливается с облаком: Blind, Curse, Despair); иначе маска — по цвету обводки (самый частый тёмный цвет)."""
    import texedit
    from scipy import ndimage as ndi
    a = np.asarray(orig.convert('RGBA')).astype(np.float32)
    al = a[:, :, 3]; op = al > 200
    if spec.get('em_fill') is not None:
        fc = np.array(spec['em_fill'][:3], np.float32)
        fm = op & (np.abs(a[:, :, :3] - fc).sum(2) < spec.get('em_fill_thr', 90))
        fm = cv2.morphologyEx(fm.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
        m = cv2.dilate(fm.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))) > 0
    else:
        L = a[:, :, :3].mean(2)
        thr = np.percentile(L[op], 20)
        cols = a[op & (L <= thr)][:, :3]
        q = (cols // 16).astype(int); key = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
        v, c = np.unique(key, return_counts=True); kk = v[c.argmax()]
        oc = np.array([kk // 256 * 16 + 8, kk // 16 % 16 * 16 + 8, kk % 16 * 16 + 8], np.float32)
        om = op & (np.abs(a[:, :, :3] - oc).sum(2) < 90)
        om = cv2.morphologyEx(om.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
        if spec.get('em_odil'):
            om = cv2.dilate(om.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * spec['em_odil'] + 1,) * 2)) > 0
        m = ndi.binary_fill_holes(om)
    if spec.get('em_box'):
        x0, y0, x1, y1 = spec['em_box']; bm = np.zeros_like(m); bm[y0:y1, x0:x1] = True; m &= bm
    m = cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    pm = np.clip(a[:, :, :3] * al[:, :, None] / 255, 0, 255).astype(np.uint8)
    r = spec.get('em_r', 9)
    ip = cv2.inpaint(np.ascontiguousarray(pm[:, :, ::-1]), m, r, cv2.INPAINT_TELEA)[:, :, ::-1].astype(np.float32)
    ia = cv2.inpaint(al.astype(np.uint8), m, r, cv2.INPAINT_TELEA).astype(np.float32)
    rgb = np.where(ia[:, :, None] > 1, ip * 255 / np.maximum(ia[:, :, None], 1), 0)
    base = Image.fromarray(np.clip(np.concatenate([rgb, ia[:, :, None]], 2), 0, 255).astype(np.uint8))
    s2 = dict(spec)
    for kk_ in ('custom', 'under'):
        s2.pop(kk_, None)
    s2['clear'] = 'keep'
    return texedit.apply_spec(base, s2)


def brush_custom(orig, spec):
    """Кистевая надпись с «грязной» синей заливкой и жёлтой смещённой обводкой (кат-ин «Awaken» в RPG):
    заливка новых букв берётся из пикселей заливки оригинала (ближайший пиксель — фактура сохраняется),
    жёлтая обводка — расширение маски + её сдвиг вправо-вниз, вокруг — мягкое белое свечение."""
    import lutfx
    from scipy import ndimage as ndi
    W, H = orig.size
    a = np.asarray(orig.convert('RGBA')).astype(np.float32)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    fill = (al > 200) & (b > 90) & (r < 110) & (b > r + 60)
    # фактура «грязной» заливки: пятна и крапинки трёх тонов оригинала (тёмный / средний / светлый)
    fc = a[fill][:, :3]; lum = fc.mean(1)
    dark, mid, light = [np.median(fc[(lum >= np.percentile(lum, lo)) & (lum <= np.percentile(lum, hi))], 0)
                        for lo, hi in ((0, 15), (40, 60), (88, 100))]
    rng = np.random.default_rng(spec.get('seed', 7))
    n1 = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 6); n1 = (n1 - n1.mean()) / (n1.std() + 1e-6)
    n2 = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.2); n2 = (n2 - n2.mean()) / (n2.std() + 1e-6)
    t = np.clip(0.5 + 0.28 * n1 + 0.22 * n2, 0, 1)[..., None]
    tex = np.where(t < 0.5, dark + (mid - dark) * (t / 0.5), mid + (light - mid) * ((t - 0.5) / 0.5)).astype(np.float32)
    s2 = dict(spec); s2.pop('custom', None)
    nm = lutfx.text_mask(s2, al > 128).astype(np.float32) / 255
    nb = nm > 0.45
    w = spec.get('br_w', 6); dx, dy = spec.get('br_shift', (10, 6))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * w + 1, 2 * w + 1))
    ym = cv2.dilate(nb.astype(np.uint8), k)
    sh = np.zeros_like(ym); sh[max(0, dy):, max(0, dx):] = ym[:H - max(0, dy), :W - max(0, dx)]
    ym = np.maximum(ym, sh).astype(np.float32)
    ym = cv2.GaussianBlur(ym, (0, 0), 0.8)
    glow = np.clip(cv2.GaussianBlur(ym, (0, 0), spec.get('br_glow', 14)) * spec.get('br_glow_gain', 1.6), 0, 1) * spec.get('br_glow_a', 0.55)
    out = np.zeros((H, W, 4), np.float32)
    def over(col, alpha):
        alpha = alpha[..., None]
        src = np.concatenate([np.broadcast_to(col, (H, W, 3)) if np.ndim(col) == 1 else col, np.ones((H, W, 1), np.float32) * 255], 2)
        o_a = out[..., 3:4] / 255
        na = alpha + o_a * (1 - alpha)
        rgb = (src[..., :3] * alpha + out[..., :3] * o_a * (1 - alpha)) / np.maximum(na, 1e-6)
        out[..., :3] = rgb; out[..., 3:4] = na * 255
    over(np.array(spec.get('br_glow_col', (255, 255, 230)), np.float32), glow)
    over(np.array(spec.get('br_col', (255, 255, 118)), np.float32), np.clip(ym, 0, 1))
    over(tex, np.clip(nm, 0, 1))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def _shift(m, dx, dy):
    """Сдвиг массива (float/bool) на (dx, dy) пикселей с заполнением нулями (дробный — билинейно)."""
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    src = m.astype(np.float32)
    return cv2.warpAffine(src, M, (m.shape[1], m.shape[0]), flags=cv2.INTER_LINEAR, borderValue=0)


def sticker_measure(a):
    """Буквы-«наклейки» (Ловля лосося: READY/GO!/FINISH!): цветная заливка, чёрная обводка, белая обводка, чёрная тень.
    Возвращает маску заливки оригинала и параметры колец: (r, sx, sy) чёрной и белой обводки, сдвиг тени, цвета."""
    from scipy import ndimage as ndi
    A = a.astype(np.float32)
    L = A[..., :3].mean(2); mx = A[..., :3].max(2); mn = A[..., :3].min(2)
    S = (mx - mn) / np.maximum(mx, 1)
    op = a[..., 3] > 128
    light = op & (L >= 120)
    n, lab = cv2.connectedComponents(light.astype(np.uint8), connectivity=4)
    core = np.zeros(op.shape, bool)
    for i in range(1, n):
        sel = lab == i
        if sel.sum() > 30 and np.median(S[sel]) > 0.3:
            core |= sel
    core = ndi.binary_closing(core, np.ones((3, 3), bool)) | core
    dout = cv2.distanceTransform((~core).astype(np.uint8), cv2.DIST_L2, 5)
    dark = op & (L < 120)
    B_obs = dark & (dout <= 12)
    W_obs = light & ~core & (S < 0.25)
    Sh_obs = dark & (dout > 12)
    info = {'core': core}

    def fit(target, excl, rr, base=None):
        best = (-1, None)
        for r in rr:
            reg = (dout <= r).astype(np.float32)
            for sx in np.arange(-1, 3.01, 0.5):
                for sy in np.arange(-1, 3.51, 0.5):
                    m = (_shift(reg, sx, sy) > 0.5) & ~excl
                    if base is not None:
                        m &= ~base
                    inter = (m & target).sum(); uni = (m | target).sum()
                    iou = inter / max(1, uni)
                    if iou > best[0]:
                        best = (iou, (r, sx, sy))
        return best
    b1 = fit(B_obs, core, np.arange(3, 11.01, 0.5))
    r1, s1x, s1y = b1[1]
    Bm = (_shift((dout <= r1).astype(np.float32), s1x, s1y) > 0.5) & ~core
    b2 = fit(W_obs, core, np.arange(8, 20.01, 0.5), base=Bm)
    r2, s2x, s2y = b2[1]
    Wfull = _shift((dout <= r2).astype(np.float32), s2x, s2y) > 0.5
    def sh_iou(dx, dy):
        m = (_shift(Wfull.astype(np.float32), dx, dy) > 0.5) & ~Wfull & ~core & ~Bm
        inter = (m & Sh_obs).sum(); uni = (m | Sh_obs).sum()
        return inter / max(1, uni)
    best = (-1, (0, 0))
    if Sh_obs.sum() > 50:
        for dx in range(-4, 26, 2):              # грубо, затем уточнение ±1
            for dy in range(-4, 32, 2):
                v = sh_iou(dx, dy)
                if v > best[0]: best = (v, (dx, dy))
        cx_, cy_ = best[1]
        for dx in range(cx_ - 1, cx_ + 2):
            for dy in range(cy_ - 1, cy_ + 2):
                v = sh_iou(dx, dy)
                if v > best[0]: best = (v, (dx, dy))
    info.update(black=(r1, s1x, s1y), white=(r2, s2x, s2y), shadow=best[1], fit=(b1[0], b2[0], best[0]))
    info['col_black'] = np.median(A[B_obs], 0) if B_obs.any() else np.array([0, 0, 0, 255], np.float32)
    info['col_white'] = np.median(A[W_obs], 0) if W_obs.any() else np.array([252, 252, 252, 255], np.float32)
    info['col_shadow'] = np.median(A[Sh_obs], 0) if Sh_obs.sum() > 20 else info['col_black']
    return info


def sticker_custom(orig, spec):
    """Новая буква в стиле «наклейки» оригинала: заливка — по таблице оригинала (lutfx.LUT, только внутри),
    чёрная и белая обводка и тень — расширения маски с подобранными по оригиналу радиусами и сдвигами."""
    import lutfx
    W, H = orig.size
    ss = spec.get('st_ss', 2)
    a0 = np.asarray(orig.convert('RGBA'))
    info = sticker_measure(a0)
    a = np.asarray(Image.fromarray(a0).resize((W * ss, H * ss), Image.BICUBIC))
    core = cv2.resize(info['core'].astype(np.uint8), (W * ss, H * ss), interpolation=cv2.INTER_NEAREST) > 0
    lut = lutfx.LUT(a, core, R=3 * ss, nv=spec.get('lx_nv', 8), nd=spec.get('lx_nd', 4), rot=spec.get('lx_rot', 0))
    r1, s1x, s1y = info['black']; r2, s2x, s2y = info['white']; shx, shy = info['shadow']
    ho = lutfx.letter_height(core)
    # поля: как у оригинала (texedit.allowed_box), надпись вместе с обводками и тенью не должна выходить за них
    import texedit
    ab = texedit.allowed_box(orig, dict(spec, fit_margin=spec.get('fit_margin', 3)))
    if spec.get('st_maxw') or spec.get('st_grow'):
        # ширина буквы целиком (с обводками) — не больше st_maxw (или ширины оригинала × st_grow), по центру оригинала:
        # буквы-спрайты стоят в анимации на своих местах, шире — наедут на соседние
        al0 = a0[..., 3] > 40
        xs0 = np.where(al0.any(0))[0]
        cx0 = (xs0.min() + xs0.max() + 1) / 2
        mw = spec.get('st_maxw') or (xs0.max() + 1 - xs0.min()) * spec['st_grow']
        ab = (max(ab[0], cx0 - mw / 2), ab[1], min(ab[2], cx0 + mw / 2), ab[3])
    cur = {}
    for it in range(30):
        s = lutfx.scale_spec(dict(spec, **cur), ss)
        nm = lutfx.text_mask(s, core) > 110
        xr = np.where(nm.any(0))[0]
        if not len(xr):
            break
        cw = (xr.max() - xr.min()) / ss              # ширина самих букв (до утолщения штриха)
        hn = lutfx.letter_height(nm)
        tgt = lutfx.half_width(core) * (hn / ho if ho and hn else 1.0) * spec.get('lx_wk', 1.0)
        nm = lutfx.match_width(nm, tgt)
        ys, xs = np.where(nm)
        # габарит наклейки: буква + белая обводка (со сдвигом) + тень
        x0 = xs.min() / ss - r2 + min(s2x, s2x + shx); x1 = xs.max() / ss + r2 + max(s2x, s2x + shx) + 1
        y0 = ys.min() / ss - r2 + min(s2y, s2y + shy); y1 = ys.max() / ss + r2 + max(s2y, s2y + shy) + 1
        if x0 >= ab[0] and y0 >= ab[1] and x1 <= ab[2] and y1 <= ab[3]:
            break
        if not spec.get('fit', True):
            break
        moved = False
        if x1 - x0 > ab[2] - ab[0]:
            cur['maxw'] = max(8, cw - (x1 - x0 - (ab[2] - ab[0])) - 1)
            moved = True
        elif x0 < ab[0]:
            cur['dx'] = cur.get('dx', spec.get('dx', 0)) + (ab[0] - x0); moved = True
        elif x1 > ab[2]:
            cur['dx'] = cur.get('dx', spec.get('dx', 0)) - (x1 - ab[2]); moved = True
        if y1 - y0 > ab[3] - ab[1]:
            cur['capscale'] = cur.get('capscale', spec.get('capscale', 1.0)) * 0.96; moved = True
        elif y0 < ab[1]:
            cur['dy'] = cur.get('dy', spec.get('dy', 0)) + (ab[1] - y0); moved = True
        elif y1 > ab[3]:
            cur['dy'] = cur.get('dy', spec.get('dy', 0)) - (y1 - ab[3]); moved = True
        if not moved:
            break
    inner = lut.render(nm, rot=spec.get('lx_rot', 0))                    # премультиплицированный
    dn = cv2.distanceTransform((~nm).astype(np.uint8), cv2.DIST_L2, 5)  # снаружи — расстояние до буквы

    def ring(r, sx, sy):
        al = np.clip(r * ss - dn + 0.5, 0, 1)
        return np.clip(_shift(al, sx * ss, sy * ss), 0, 1)
    Bk = ring(r1, s1x, s1y); Wt = ring(r2, s2x, s2y); Sh = np.clip(_shift(Wt, shx * ss, shy * ss), 0, 1)
    out = np.zeros((H * ss, W * ss, 4), np.float32)

    def over(col, alpha):
        c = np.asarray(col, np.float32)
        aa = alpha[..., None] * (c[3] / 255.0)
        out[..., :3] = c[:3] * aa + out[..., :3] * (1 - aa)
        out[..., 3:4] = 255 * aa + out[..., 3:4] * (1 - aa)
    over(info['col_shadow'], Sh)
    over(info['col_white'], Wt)
    over(info['col_black'], Bk)
    # заливка (премультиплицированная) поверх, внутри буквы + 1 px сглаживания
    din = cv2.distanceTransform(nm.astype(np.uint8), cv2.DIST_L2, 5)
    k = np.clip(din - dn + 0.5, 0, 1)[..., None]
    ia = inner[..., 3:4] / 255.0
    rgb = np.where(ia > 1e-3, inner[..., :3] / np.maximum(ia, 1e-3), 0)
    out[..., :3] = rgb * k + out[..., :3] * (1 - k)
    out[..., 3:4] = np.maximum(out[..., 3:4], 255 * k)
    pm = out.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
    small = cv2.resize(pm, (W, H), interpolation=cv2.INTER_AREA)
    return Image.fromarray(lutfx.unpremul(small))
