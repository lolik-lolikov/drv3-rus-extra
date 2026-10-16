"""Пиксельный шрифт надписи SCORE в «Монолите» (t_casino_hkt_score_tx_DXT1_US): буквы 8×10 пикселей арта,
обводка в 1 пиксель (4-связная), палитра из 4 цветов, пиксель арта = 4×4 пикселя текстуры, шаг букв 11.

Затенение как у оригинала: верхний край заливки — светлый (c), нижний — тёмно-жёлтый (g), остальное — жёлтый (y);
на «диагональных» углах верхний край остаётся жёлтым."""
import numpy as np
from PIL import Image

PAL = {'o': (78, 60, 70, 255), 'c': (247, 237, 177, 255), 'y': (239, 219, 98, 255), 'g': (222, 183, 0, 255)}

GLYPHS = {
    'О': ['.XXXXXX.',
          'XXX..XXX',
          'XX....XX',
          'XX....XX',
          'XX....XX',
          'XX....XX',
          'XX....XX',
          'XXX..XXX',
          'XXXXXXXX',
          '.XXXXXX.'],
    'Ч': ['XX....XX',
          'XX....XX',
          'XX....XX',
          'XX....XX',
          'XXX..XXX',
          'XXXXXXXX',
          '.XXXXXXX',
          '......XX',
          '......XX',
          '......XX'],
    'К': ['XX....XX',
          'XX...XXX',
          'XX..XXX.',
          'XX.XXX..',
          'XXXXX...',
          'XXXXX...',
          'XX.XXX..',
          'XX..XXX.',
          'XX...XXX',
          'XX....XX'],
    'И': ['XX....XX',
          'XX....XX',
          'XX...XXX',
          'XX..XXXX',
          'XX.XX.XX',
          'XXXX..XX',
          'XXX...XX',
          'XX....XX',
          'XX....XX',
          'XX....XX'],
}


def art(text, W=64, H=16, x0=0, y0=3, adv=11):
    """Холст арта (H×W символов): x0 — левый край первой клетки (обводка), y0 — верхняя строка заливки."""
    fill = np.zeros((H, W), bool)
    x = x0
    for ch in text:
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c_, v in enumerate(row):
                if v == 'X':
                    fill[y0 + r, x + 1 + c_] = True
        x += adv
    P = np.pad(fill, 1)
    up = P[:-2, 1:-1]; dn = P[2:, 1:-1]; lf = P[1:-1, :-2]; rt = P[1:-1, 2:]
    ul = P[:-2, :-2]; ur = P[:-2, 2:]
    outline = (~fill) & (up | dn | lf | rt)
    # внешняя область (не дырки букв): исключение для диагональных углов действует только снаружи
    import cv2
    n, lab = cv2.connectedComponents((~np.pad(fill, 1)).astype(np.uint8), connectivity=4)
    ext = (lab == lab[0, 0])
    up_ext = ext[:-2, 1:-1]
    top = fill & ~up
    diag = ((~lf & ur) | (~rt & ul)) & up_ext
    c = top & ~diag
    g = fill & ~dn & ~c
    out = np.zeros((H, W, 4), np.uint8)
    out[outline] = PAL['o']
    out[fill] = PAL['y']
    out[g] = PAL['g']
    out[c] = PAL['c']
    return out


def score_custom(orig, spec):
    k = spec.get('pixel', 4)
    W0, H0 = orig.size
    a = art(spec['text'], W0 // k, H0 // k, spec.get('pg_x0', 0), spec.get('pg_y0', 3), spec.get('pg_adv', 11))
    big = np.repeat(np.repeat(a, k, 0), k, 1)
    return Image.fromarray(big)
