"""Пиксельные надписи «Монолита» (пиксель-арт, увеличенный в k раз без сглаживания).

Устройство оригинальных букв (в пикселях арта): цветная «сердцевина» с вертикальным градиентом и косыми полосами,
вокруг неё кольца: 1 px тёмная линия, 2 px светлый ободок, 1 px тёмная обводка, снизу — тень.
Новая надпись строится так же: сердцевина — буквы шрифта (по одной, с ровными промежутками), кольца — по расстоянию
от сердцевины, цвета каждого кольца (с учётом стороны), заливки (по высоте и фазе полос) и тени снимаются с оригинала.

pixword_custom(orig, spec): spec — text, font, pixel (k), и необязательные:
  pw_cap      — высота сердцевины заглавных (пиксели арта), по умолчанию — как у оригинала;
  pw_gap      — промежуток между сердцевинами соседних букв (по умолчанию — как у оригинала);
  pw_space    — ширина пробела (в пикселях арта), pw_hscale — сжатие букв по ширине;
  pw_period   — период косых полос по x+y (5); pw_rings — число колец ('auto' — как у оригинала); pw_shadow — (dx, dy) тени;
  pw_center   — центр надписи (x, y) в пикселях текстуры (по умолчанию — центр надписи оригинала);
  pw_core_sel — 'sat' (насыщенная заливка) | ('lum', порог) — как найти сердцевину оригинала."""
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont


def grid_phase(a, k):
    A = a.astype(np.int32)
    dx = np.any(np.abs(np.diff(A, axis=1)) > 30, axis=2)
    dy = np.any(np.abs(np.diff(A, axis=0)) > 30, axis=2)
    hx = np.bincount((np.where(dx)[1] + 1) % k, minlength=k)
    hy = np.bincount((np.where(dy)[0] + 1) % k, minlength=k)
    return int(np.argmax(hx)), int(np.argmax(hy))


def core_mask(a, sel='sat'):
    al = a[:, :, 3] > 128
    A = a[:, :, :3].astype(np.float32)
    mx = A.max(2); mn = A.min(2)
    if sel == 'inside':
        # всё внутри тёмного кольца вокруг букв: не белое (наклейка) и не прозрачное, на расстоянии > 1.5 от них
        S = (mx - mn) / np.maximum(mx, 1)
        white = al & (S < 0.18) & (mx > 185)
        bg = (~al) | white
        d = cv2.distanceTransform((~bg).astype(np.uint8), cv2.DIST_L2, 3)
        return d > 1.5
    if sel == 'sat':
        # яркая насыщенная заливка (тёмно-коричневые обводки тоже «насыщенные», но тёмные — их отсекает порог яркости)
        S = (mx - mn) / np.maximum(mx, 1)
        thr = 0.62 * np.percentile(mx[al], 95) if al.any() else 140
        m = al & (S > 0.32) & (mx > thr)
    else:
        m = al & (mx > sel[1])
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
    inv = (~m).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, n):
        if st[i, 4] < 14 and st[i, 0] > 0 and st[i, 1] > 0:
            m[lab == i] = True
    return m


def ring_dist(m):
    """Расстояние снаружи от сердцевины (L2, округлённое): 0 внутри, 1,2,3... снаружи."""
    d = cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 3)
    return np.where(m, 0, np.ceil(d - 0.3)).astype(np.int32)


def side_of(m, nsec=4):
    """Сторона от сердцевины для каждой точки снаружи: 0 — верх, 1 — право, 2 — низ, 3 — лево (по направлению градиента)."""
    d = cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 5)
    g = cv2.GaussianBlur(d, (0, 0), 1.2)
    gy, gx = np.gradient(g)
    ang = np.arctan2(gy, gx)        # направление наружу (y вниз)
    # 0: вверх (-pi/2), 1: вправо (0), 2: вниз (pi/2), 3: влево (pi)
    sec = np.round((ang + np.pi / 2) / (np.pi / 2)).astype(np.int32) % 4
    return sec


def letter_rows(m):
    ys = np.where(m.any(1))[0]
    return (int(ys.min()), int(ys.max()) + 1) if len(ys) else (0, m.shape[0])


def measure(a, sel='sat', rings='auto', period=5, nb=12, exclude=None):
    """Снять с оригинала (массив арта RGBA) таблицы цветов. exclude — маска, которую не учитывать (картинки, сердечко).
    rings='auto' — число колец обводки определяется по левой стороне букв (до первого кольца, где непрозрачных < 50%)."""
    m = core_mask(a, sel)
    if exclude is not None:
        m &= ~exclude
    H, W = m.shape
    rd = ring_dist(m)
    sd = side_of(m)
    y0, y1 = letter_rows(m)
    A = a.astype(np.float32)
    info = {'core_h': y1 - y0, 'y0': y0, 'y1': y1}
    # заливка: по высоте (nb полос) и фазе (x+y) mod period
    yy, xx = np.mgrid[0:H, 0:W]
    vb = np.clip(((yy - y0) / max(1, y1 - y0 - 1) * nb).astype(int), 0, nb - 1)
    ph = (xx + yy) % period
    fill = np.zeros((nb, period, 4), np.float32); have = np.zeros((nb, period), bool)
    inner = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    for b in range(nb):
        for p in range(period):
            s = inner & (vb == b) & (ph == p)
            if s.sum() < 2:
                s = m & (vb == b) & (ph == p)
            if s.sum() >= 2:
                fill[b, p] = np.median(A[s], 0); have[b, p] = True
    for b in range(nb):
        for p in range(period):
            if not have[b, p]:
                cand = [(abs(b - b2) + 0.1 * abs(p - p2), b2, p2) for b2 in range(nb) for p2 in range(period) if have[b2, p2]]
                if cand:
                    _, b2, p2 = min(cand); fill[b, p] = fill[b2, p2]
    info['fill'] = fill; info['period'] = period
    # кольца 1..rings по сторонам; картинки (exclude) не учитываются, кроме точек вплотную к буквам (обводка поверх картинки)
    opaque = a[:, :, 3] > 128
    valid = np.ones((H, W), bool) if exclude is None else ~(exclude & (rd > 8))
    if rings == 'auto':
        rings = 1
        for r in range(1, 9):
            fr = []
            for s_ in (3, 0):
                sel_ = (rd == r) & (sd == s_) & valid
                if sel_.sum() >= 10:
                    fr.append(opaque[sel_].mean())
            if fr and min(fr) >= 0.5:
                rings = r
            else:
                break
    ok_px = opaque & valid
    ring = np.zeros((rings + 1, 4, 4), np.float32); rhave = np.zeros((rings + 1, 4), bool)
    for r in range(1, rings + 1):
        for s_ in range(4):
            sel_ = (rd == r) & (sd == s_) & valid
            n = sel_.sum()
            if n >= 3:
                if opaque[sel_].mean() < 0.5:
                    ring[r, s_] = 0; rhave[r, s_] = True
                elif (sel_ & opaque).sum() >= 3:
                    ring[r, s_] = np.median(A[sel_ & opaque], 0); rhave[r, s_] = True
        for s_ in range(4):
            if not rhave[r, s_]:
                ok = [t for t in range(4) if rhave[r, t]]
                if ok: ring[r, s_] = ring[r, ok[0]]
    info['ring'] = ring; info['rings'] = rings
    # тень: непрозрачные точки дальше колец
    shadow_px = (rd > rings) & ok_px
    info['shadow_col'] = np.median(A[shadow_px], 0) if shadow_px.sum() > 5 else np.array([40, 10, 10, 255], np.float32)
    # смещение тени: насколько ниже/правее колец простирается непрозрачное
    full = rd <= rings
    best = (0, 0, -1)
    for dy in range(0, 7):
        for dx in range(-2, 4):
            sh = np.zeros_like(full); sh[dy:, max(0, dx):W + min(0, dx)] = full[:H - dy, max(0, -dx):W - max(0, dx)] if dx >= 0 else full[:H - dy, -dx:]
            cov = (sh & shadow_px).sum() - 0.3 * (sh & ~full & ~shadow_px & (a[:, :, 3] <= 128)).sum()
            if cov > best[2]: best = (dx, dy, cov)
    info['shadow'] = (best[0], best[1])
    # промежуток между сердцевинами соседних букв
    cols = m.any(0)
    runs = []; x = 0
    while x < W:
        if cols[x]:
            s0 = x
            while x < W and cols[x]: x += 1
            runs.append((s0, x))
        x += 1
    gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
    info['gap'] = int(np.median(gaps)) if gaps else 8
    xs = np.where(m.any(0))[0]
    info['x0'], info['x1'] = (int(xs.min()), int(xs.max()) + 1) if len(xs) else (0, W)
    info['core'] = m; info['rd'] = rd; info['sd'] = sd
    return info


def glyph_masks(text, font, cap, hscale=1.0, ss=8, sprites=None):
    """Маски букв (bool) высотой сердцевины cap пикселей; возвращает список (mask, dy от верха заглавных).
    sprites: {символ: (mask, top_cap)} — готовые маски (например, сердечко из оригинала)."""
    sprites = sprites or {}
    ref = ImageFont.truetype(font, 1000)
    capref = -ref.getbbox('Н', anchor='ls')[1]
    size = cap * ss * 1000 / capref
    f = ImageFont.truetype(font, max(4, int(round(size))))
    out = []
    for ch in text:
        if ch == ' ':
            out.append(None); continue
        if ch in sprites:
            out.append(sprites[ch]); continue
        bb = f.getbbox(ch, anchor='ls')
        w = bb[2] - bb[0] + 4 * ss; h = int(cap * ss * 1.6) + 4 * ss
        im = Image.new('L', (int(w), h), 0)
        base = int(cap * ss * 1.25) + 2 * ss
        ImageDraw.Draw(im).text((2 * ss - bb[0], base), ch, font=f, fill=255, anchor='ls')
        a = np.array(im)
        xs = np.where(a.max(0) > 0)[0]
        a = a[:, xs.min():xs.max() + 1]
        nw = max(1, int(round(a.shape[1] / ss * hscale)))
        small = cv2.resize(a.astype(np.float32), (nw, int(round(a.shape[0] / ss))), interpolation=cv2.INTER_AREA)
        m = small > 127
        top_cap = (base - int(cap * ss)) / ss       # строка верха заглавных в маске
        out.append((m, top_cap))
    return out


def compose_core(text, font, cap, gap, space, hscale, H, W, cx, cy_top, sprites=None, placed=None):
    gl = glyph_masks(text, font, cap, hscale, sprites=sprites)
    widths = [g[0].shape[1] if g is not None else space for g in gl]
    total = sum(widths) + gap * (len([g for g in gl if g is not None]) - 1)
    # пробел: вместо промежутка
    x = int(round(cx - total / 2))
    m = np.zeros((H, W), bool)
    prev_letter = False
    for g, w in zip(gl, widths):
        if g is None:
            x += space; prev_letter = False; continue
        gm, top_cap = g
        if prev_letter:
            x += gap
        y = int(round(cy_top - top_cap))
        h_, w_ = gm.shape
        ys0, xs0 = max(0, y), max(0, x)
        ys1, xs1 = min(H, y + h_), min(W, x + w_)
        if ys1 > ys0 and xs1 > xs0:
            m[ys0:ys1, xs0:xs1] |= gm[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
        if placed is not None and sprites:
            placed.append((x, y, g))
        x += w_; prev_letter = True
    return m


def render(info, m, shape):
    H, W = shape
    rings = info['rings']
    rd = ring_dist(m)
    sd = side_of(m)
    out = np.zeros((H, W, 4), np.float32)
    # тень (под всем)
    full = rd <= rings
    dx, dy = info['shadow']
    sh = np.zeros_like(full)
    if dy or dx:
        ys = slice(dy, H); xs_dst = slice(max(0, dx), W + min(0, dx)); xs_src = slice(max(0, -dx), W - max(0, dx))
        sh[ys, xs_dst] = full[:H - dy, xs_src]
        sh &= ~full
        out[sh] = info['shadow_col']
    # кольца
    for r in range(1, rings + 1):
        for s_ in range(4):
            sel = (rd == r) & (sd == s_)
            out[sel] = info['ring'][r, s_]
    # заливка
    y0, y1 = letter_rows(m)
    yy, xx = np.mgrid[0:H, 0:W]
    nb = info['fill'].shape[0]
    vb = np.clip(((yy - y0) / max(1, y1 - y0 - 1) * nb).astype(int), 0, nb - 1)
    ph = (xx + yy) % info['period']
    out[m] = info['fill'][vb[m], ph[m]]
    return np.clip(out, 0, 255).astype(np.uint8)


def pixword_custom(orig, spec):
    import texedit
    W0, H0 = orig.size
    k = spec.get('pixel', 4)
    a = np.asarray(orig.convert('RGBA'))
    ph = spec.get('pixel_phase') or grid_phase(a, k)
    ox = (ph[0] + k // 2) % k; oy = (ph[1] + k // 2) % k
    s = a[oy::k, ox::k]
    H, W = s.shape[:2]
    exclude = None
    sprites = {}; sprite_src = {}; sprite_pos = {}
    # сердечко и т.п.: прямоугольник в пикселях текстуры -> маска (насыщенные пиксели) и цвета оригинала
    for ch, (bx0, by0, bx1, by1) in (spec.get('pw_sprites') or {}).items():
        X0, Y0, X1, Y1 = max(0, (bx0 - ox) // k), max(0, (by0 - oy) // k), (bx1 - ox) // k + 1, (by1 - oy) // k + 1
        reg = np.zeros(s.shape[:2], bool); reg[Y0:Y1, X0:X1] = True
        cm = core_mask(s, spec.get('pw_core_sel', 'sat')) & reg
        ys_, xs_ = np.where(cm)
        sm = cm[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]
        sprite_src[ch] = s[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1].copy()
        sprite_pos[ch] = (ys_.min(), xs_.min())
        exclude = reg if exclude is None else (exclude | reg)
        sprites[ch] = (sm, ys_.min())            # положение по вертикали — абсолютное (как у оригинала)
    if spec.get('pw_exclude'):
        for bx0, by0, bx1, by1 in spec['pw_exclude']:
            reg = np.zeros(s.shape[:2], bool)
            reg[max(0, (by0 - oy) // k):max(0, (by1 - oy) // k + 1), max(0, (bx0 - ox) // k):max(0, (bx1 - ox) // k + 1)] = True
            exclude = reg if exclude is None else (exclude | reg)
    info = measure(s, spec.get('pw_core_sel', 'sat'), spec.get('pw_rings', 'auto'), spec.get('pw_period', 5), spec.get('pw_nb', 12), exclude)
    if spec.get('pw_shadow') is not None:
        info['shadow'] = tuple(spec['pw_shadow'])
    cap = spec.get('pw_cap') or info['core_h']
    gap = spec.get('pw_gap', info['gap'])
    space = spec.get('pw_space', int(cap * 0.45) + 2 * gap)
    font = texedit.FONTS[spec.get('font', 'rubik9')]
    if spec.get('pw_center'):
        cx = spec['pw_center'][0] / k
    else:
        cx = (info['x0'] + info['x1']) / 2
    cy_top = info['y0'] + spec.get('pw_dy', 0)
    hs = spec.get('pw_hscale', 1.0)
    maxw = spec.get('pw_maxw') or min(W - 2 * (info['rings'] + 3), (info['x1'] - info['x0']) * spec.get('pw_grow', 1.25))
    # спрайты: «верх заглавных» для них — так, чтобы их абсолютная строка совпала с оригиналом
    sp2 = {ch: (sm, cy_top - y_abs) for ch, (sm, y_abs) in sprites.items()}
    for _ in range(20):
        placed = []
        m = compose_core(spec['text'], font, cap, gap, space, hs, H, W, cx, cy_top, sp2, placed)
        xs = np.where(m.any(0))[0]
        if not len(xs) or xs.max() - xs.min() + 1 <= maxw:
            break
        hs *= 0.95
    img = render(info, m, (H, W))
    y_off = oy - k // 2; x_off = ox - k // 2
    Y, X = np.mgrid[0:H0, 0:W0]
    iy = (Y - y_off) // k; ix = (X - x_off) // k; sub_y = (Y - y_off) % k; sub_x = (X - x_off) % k
    inside = (iy >= 0) & (iy < H) & (ix >= 0) & (ix < W)
    iyc = np.clip(iy, 0, H - 1); ixc = np.clip(ix, 0, W - 1)

    def up(arr):
        """Арт -> пиксели текстуры (блоки k×k)."""
        o_ = arr[iyc, ixc].copy()
        o_[~inside] = 0
        return o_

    rings = info['rings']
    big = up(img).astype(np.float32)
    if spec.get('pw_sub', True):
        # подпиксельный рельеф оригинала (тёмная строка-«развёртка» в каждом пикселе арта, выпуклый белый ободок):
        # отношение яркости пикселя текстуры к яркости центра его пикселя арта — по (кольцо, сторона, строка, столбец в блоке)
        cat_o = np.clip(info['rd'], 0, rings + 1); sd_o = np.where(cat_o > 0, info['sd'], 0)
        lum_t = a[:, :, :3].astype(np.float32).mean(2)
        lum_c = s[:, :, :3].astype(np.float32).mean(2)[iyc, ixc]
        ok = inside & (a[:, :, 3] > 128) & (s[:, :, 3][iyc, ixc] > 128) & (lum_c > 12)
        if exclude is not None:
            ok &= ~exclude[iyc, ixc]
        ratio = (lum_t / np.maximum(lum_c, 1))[ok]
        C = cat_o[iyc, ixc][ok]; S_ = sd_o[iyc, ixc][ok]; SB = (sub_y * k + sub_x)[ok]
        T = np.ones((rings + 2, 4, k * k), np.float32)
        for c_ in range(rings + 2):
            selc = C == c_
            for s_ in range(4):
                sel_cs = selc & (S_ == s_)
                if sel_cs.sum() < 8 * k * k:
                    sel_cs = selc
                rv = ratio[sel_cs]; sb = SB[sel_cs]
                for q in range(k * k):
                    v = rv[sb == q]
                    if len(v) >= 5:
                        T[c_, s_, q] = np.median(v)
        T = T.reshape(rings + 2, 4, k, k)
        T = np.clip(T, 0.3, 2.0)
        rd_n = np.clip(ring_dist(m), 0, rings + 1); sd_n = np.where(rd_n > 0, side_of(m), 0)
        fac = T[rd_n[iyc, ixc], sd_n[iyc, ixc], sub_y, sub_x]
        big[:, :, :3] *= fac[:, :, None]
    big = np.clip(big, 0, 255)
    # спрайты (сердечко и т.п.) — пиксели текстуры оригинала блоками
    for (x, y, g) in placed:
        for ch, (sm, tc) in sp2.items():
            if g[0] is sm:
                sy0, sx0 = sprite_pos[ch]
                h_, w_ = sm.shape
                tgt = np.zeros((H, W), bool)
                ys0, xs0 = max(0, y), max(0, x); ys1, xs1 = min(H, y + h_), min(W, x + w_)
                tgt[ys0:ys1, xs0:xs1] = sm[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
                T_ = up(tgt.astype(np.uint8)) > 0
                src_y = Y + (sy0 - y) * k; src_x = X + (sx0 - x) * k
                T_ &= (src_y >= 0) & (src_y < H0) & (src_x >= 0) & (src_x < W0)
                big[T_] = a[src_y[T_], src_x[T_]]
    if spec.get('pw_erase'):
        # картинка над надписью остаётся (в пикселях текстуры оригинала): стираем только зону старой надписи и кладём новую поверх
        oc = core_mask(s, spec.get('pw_core_sel', 'sat'))
        if exclude is not None: oc &= ~exclude
        zone = ring_dist(oc) <= rings + max(1, abs(info['shadow'][1])) + spec.get('pw_erase_extra', 1)
        zone &= np.arange(H)[:, None] >= info['y0'] - rings - 1
        base = a.astype(np.float32).copy(); base[up(zone.astype(np.uint8)) > 0] = 0
        al = big[:, :, 3:4] / 255
        comp = big * al + base * (1 - al); comp[:, :, 3] = np.maximum(big[:, :, 3], base[:, :, 3])
        big = comp
    out = np.clip(big, 0, 255).astype(np.uint8)
    res = Image.fromarray(out)
    for kb in spec.get('pw_keep') or []:
        res.paste(orig.crop(kb), (kb[0], kb[1]))
    return res
