"""Квадратный «цифровой» шрифт (как HELP/LIST/LUCKY! у Автомата Мономоно): буквы собираются из прямоугольников
и наклонных полос на сетке. Нужен, потому что готовых шрифтов с кириллицей такого вида нет.

Буква: функция (w, h, v, t, d) -> список фигур в пикселях:
  ('r', x0, y0, x1, y1) — прямоугольник; ('l', xa, ya, xb, yb, k) — полоса толщиной k между точками.
  w, h — ширина и высота буквы, v — толщина вертикальных штрихов, t — горизонтальных, d — выносной элемент вниз.
square_custom(orig, spec) — custom-функция для tex_specs: spec['sq'] = dict(text, h, top, v, t, gap, d, widths, x0|cx, align)."""
from PIL import Image, ImageDraw
import numpy as np
import math


def _band(xa, ya, xb, yb, k):
    dx, dy = xb - xa, yb - ya
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * k / 2, dx / L * k / 2
    return [(xa + nx, ya + ny), (xb + nx, yb + ny), (xb - nx, yb - ny), (xa - nx, ya - ny)]


def G_P(w, h, v, t, d):   # П
    return [('r', 0, 0, v, h), ('r', w - v, 0, w, h), ('r', 0, 0, w, t)]


def G_O(w, h, v, t, d):   # О
    return [('r', 0, 0, v, h), ('r', w - v, 0, w, h), ('r', 0, 0, w, t), ('r', 0, h - t, w, h)]


def G_S(w, h, v, t, d):   # С
    return [('r', 0, 0, v, h), ('r', 0, 0, w, t), ('r', 0, h - t, w, h)]


def G_M(w, h, v, t, d):   # М (квадратная: как «П» со средней ножкой до середины)
    c = (w - v) / 2
    return [('r', 0, 0, v, h), ('r', w - v, 0, w, h), ('r', 0, 0, w, t), ('r', c, 0, c + v, h * 0.62)]


def G_SHCH(w, h, v, t, d):   # Щ
    c = (w - v) / 2
    return [('r', 0, 0, v, h), ('r', c, 0, c + v, h), ('r', w - v, 0, w, h), ('r', 0, h - t, w, h), ('r', w - v, h - t, w, h + d)]


def G_SOFT(w, h, v, t, d):   # Ь
    m = h * 0.42
    return [('r', 0, 0, v, h), ('r', 0, m, w, m + t), ('r', w - v, m, w, h), ('r', 0, h - t, w, h)]


def G_I(w, h, v, t, d):   # И
    return [('r', 0, 0, v, h), ('r', w - v, 0, w, h), ('l', v * 0.5, h - v * 0.55, w - v * 0.5, v * 0.55, v * 1.08)]


def G_K(w, h, v, t, d):   # К (как K в оригинальном LUCKY!: верхний и нижний отрезки справа, ступенька посередине)
    m = h / 2
    xb = w * 0.5
    return [('r', 0, 0, v, h), ('r', 0, m - t / 2, xb, m + t / 2),
            ('r', w - v, 0, w, h * 0.3), ('r', w - v, h * 0.7, w, h),
            ('l', xb - v * 0.2, m, w - v * 0.5, h * 0.3 - v * 0.2, v * 1.0),
            ('l', xb - v * 0.2, m, w - v * 0.5, h * 0.7 + v * 0.2, v * 1.0)]


def G_U(w, h, v, t, d):   # У
    m = h * 0.5
    return [('r', 0, 0, v, m + t / 2), ('r', w - v, 0, w, h), ('r', 0, m - t / 2, w, m + t / 2), ('r', 0, h - t, w, h)]


def G_CH(w, h, v, t, d):   # Ч
    m = h * 0.5
    return [('r', 0, 0, v, m + t / 2), ('r', w - v, 0, w, h), ('r', 0, m - t / 2, w, m + t / 2)]


def G_D(w, h, v, t, d):   # Д
    i = w * 0.14
    return [('r', i, 0, i + v, h), ('r', i, 0, w, t), ('r', w - v, 0, w, h), ('r', 0, h - t, w, h),
            ('r', 0, h - t, v * 0.9, h + d), ('r', w - v * 0.9, h - t, w, h + d)]


def G_A(w, h, v, t, d):   # А
    m = h * 0.5
    return [('r', 0, 0, v, h), ('r', w - v, 0, w, h), ('r', 0, 0, w, t), ('r', 0, m - t / 2, w, m + t / 2)]


def G_N(w, h, v, t, d):   # Н
    m = h * 0.5
    return [('r', 0, 0, v, h), ('r', w - v, 0, w, h), ('r', 0, m - t / 2, w, m + t / 2)]


def G_L(w, h, v, t, d):   # Л (квадратная: «П» с чуть отогнутой левой ножкой)
    i = w * 0.18
    return [('r', i, 0, i + v, h - t), ('r', 0, h - t, i + v, h), ('r', i, 0, w, t), ('r', w - v, 0, w, h)]


def G_E(w, h, v, t, d):   # Е
    m = h * 0.5
    return [('r', 0, 0, v, h), ('r', 0, 0, w, t), ('r', 0, m - t / 2, w * 0.8, m + t / 2), ('r', 0, h - t, w, h)]


def G_R(w, h, v, t, d):   # Р
    m = h * 0.58
    return [('r', 0, 0, v, h), ('r', 0, 0, w, t), ('r', w - v, 0, w, m), ('r', 0, m - t, w, m)]


def G_T(w, h, v, t, d):   # Т
    c = (w - v) / 2
    return [('r', 0, 0, w, t), ('r', c, 0, c + v, h)]


def G_V(w, h, v, t, d):   # В
    m = h * 0.5
    return [('r', 0, 0, v, h), ('r', 0, 0, w * 0.86, t), ('r', w * 0.86 - v, 0, w * 0.86, m), ('r', 0, m - t / 2, w, m + t / 2),
            ('r', w - v, m - t / 2, w, h), ('r', 0, h - t, w, h)]


def G_Y(w, h, v, t, d):   # Ы
    m = h * 0.42; ww = w * 0.62
    return [('r', 0, 0, v, h), ('r', 0, m, ww, m + t), ('r', ww - v, m, ww, h), ('r', 0, h - t, ww, h), ('r', w - v, 0, w, h)]


def G_G(w, h, v, t, d):   # Г
    return [('r', 0, 0, v, h), ('r', 0, 0, w, t)]


def G_EXCL(w, h, v, t, d):   # !
    return [('r', 0, 0, w, h * 0.66), ('r', 0, h - t, w, h)]


def G_DOT(w, h, v, t, d):   # .
    return [('r', 0, h - t, w, h)]


def G_COLON(w, h, v, t, d):   # :
    return [('r', 0, h * 0.2, w, h * 0.2 + t), ('r', 0, h - t, w, h)]


def G_YO(w, h, v, t, d):   # Ё (точки — квадратики над буквой)
    q = max(3.0, t * 0.8); g = max(2.0, t * 0.45)
    return G_E(w, h, v, t, d) + [('r', w * 0.12, -g - q, w * 0.12 + q, -g), ('r', w * 0.62, -g - q, w * 0.62 + q, -g)]


GLYPHS = {'П': G_P, 'О': G_O, 'С': G_S, 'М': G_M, 'Щ': G_SHCH, 'Ь': G_SOFT, 'И': G_I, 'К': G_K, 'У': G_U, 'Ч': G_CH,
          'Д': G_D, 'А': G_A, 'Н': G_N, 'Л': G_L, 'Е': G_E, 'Р': G_R, 'Т': G_T, 'В': G_V, 'Ы': G_Y, 'Г': G_G,
          'Ё': G_YO, '!': G_EXCL, '.': G_DOT, ':': G_COLON}
NARROW = {'!': 'v', '.': 'v', ':': 'v'}


def render(text, h, v, t, d=0, gap=4, widths=None, default_w=None, ss=4):
    """Маска (L) надписи и список ячеек букв (x0, x1). Начало координат: верх букв = d_top (ss-пиксели)."""
    widths = widths or {}
    dw = default_w or h * 0.68
    cells = []; x = 0.0
    for ch in text:
        if ch == ' ':
            x += widths.get(' ', dw * 0.5); continue
        w = widths.get(ch, v if ch in NARROW else dw)
        cells.append((ch, x, w)); x += w + gap
    total = x - gap
    W = int(math.ceil(total * ss)) + 4 * ss; H = int(math.ceil((h + d) * ss)) + 4 * ss + 16 * ss
    m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
    o = 2 * ss; oy = 18 * ss
    for ch, x0, w in cells:
        for sh in GLYPHS[ch](w, h, v, t, d):
            if sh[0] == 'r':
                _, a, b, c, e = sh
                dr.rectangle([o + (x0 + a) * ss, oy + b * ss, o + (x0 + c) * ss - 1, oy + e * ss - 1], fill=255)
            else:
                _, xa, ya, xb, yb, k = sh
                dr.polygon([(o + (x0 + px) * ss, oy + py * ss) for px, py in _band(xa, ya, xb, yb, k)], fill=255)
    return m, total, (o, oy)


def square_mask(size, spec):
    """Маска размера текстуры. spec['sq']: text, h, top, v, t, d, gap, widths, default_w; x0 (левый край) или cx (центр)."""
    W, H = size
    q = spec['sq']
    ss = 4
    m, total, (o, oy) = render(q['text'], q['h'], q['v'], q['t'], q.get('d', 0), q.get('gap', 4), q.get('widths'), q.get('default_w'), ss)
    if 'x0' in q:
        x0 = q['x0']
    elif 'x1' in q:
        x0 = q['x1'] - total
    else:
        x0 = q.get('cx', W / 2) - total / 2
    big = Image.new('L', (W * ss, H * ss), 0)
    big.paste(m, (int(round(x0 * ss)) - o, int(round(q['top'] * ss)) - oy))
    return big.resize((W, H), Image.LANCZOS)


def square_custom(orig, spec):
    import texedit
    W, H = orig.size
    mask = square_mask((W, H), spec)
    base = Image.new('RGBA', (W, H), tuple(spec.get('basefill', (0, 0, 0, 0))))
    s2 = dict(spec)
    if s2.get('gradient') == 'orig':
        s2['gradient'] = texedit.orig_gradient(orig, s2.get('grad_box'), s2.get('grad_erode', 1), s2.get('grad_bins', 8), s2.get('grad_lum'))
    lay = texedit.style(mask, s2, (W, H))
    return Image.alpha_composite(base, lay)
