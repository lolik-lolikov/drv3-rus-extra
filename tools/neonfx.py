"""Неоновые трубки-контуры (надпись MONOKUMA в ainori_sindan): замена отдельных букв.

Новая буква задаётся силуэтом (многоугольники); трубка — полоса шириной tw вдоль края силуэта изнутри.
Свечение и цвет трубки — по таблице оригинала (цвет от расстояния до сердцевины трубки, lutfx.LUT).
Старая буква стирается: точки, ближайшая сердцевина которых принадлежит её трубкам (в радиусе свечения R);
новая кладётся поверх (максимум по каналам — свечение соседних букв не пропадает).

neon_custom(orig, spec): spec['nr_letters'] = [dict(cell=(x0,y0,x1,y1) — где старая буква, polys=[[(x,y),...],...],
  tw=4 — толщина трубки, gaps=[(x,y,r),...] — разрывы трубки)], nr_core_r — порог красного канала для сердцевины (60),
  nr_R — радиус свечения (28)."""
import numpy as np
import cv2
from PIL import Image, ImageDraw
import lutfx


def neon_custom(orig, spec):
    W, H = orig.size
    ss = spec.get('nr_ss', 4)
    A = np.asarray(orig.convert('RGBA'))
    a = A.astype(np.float32)
    core = (a[:, :, 0] > spec.get('nr_core_r', 60)) & (a[:, :, 3] > 150)
    R = spec.get('nr_R', 28)
    lut = lutfx.LUT(A, core, R=R, nv=1, nd=1)
    pm = a.copy(); pm[:, :, :3] *= pm[:, :, 3:4] / 255.0
    n, lab = cv2.connectedComponents(core.astype(np.uint8), connectivity=8)
    newtube = np.zeros((H, W), bool)
    erase_all = np.zeros((H, W), bool); old_all = np.zeros((H, W), bool)
    for L in spec['nr_letters']:
        x0, y0, x1, y1 = L['cell']
        ids = [i for i in np.unique(lab[y0:y1, x0:x1]) if i and (lab[y0:y1, x0:x1] == i).sum() > 0.8 * (lab == i).sum()]
        old = np.isin(lab, ids)
        others = core & ~old
        d_old = cv2.distanceTransform((~old).astype(np.uint8), cv2.DIST_L2, 5)
        d_oth = cv2.distanceTransform((~others).astype(np.uint8), cv2.DIST_L2, 5)
        erase_all |= (d_old < d_oth) & (d_old <= R)
        old_all |= old
        S = Image.new('L', (W * ss, H * ss), 0); dr = ImageDraw.Draw(S)
        for poly in L['polys']:
            dr.polygon([(x * ss, y * ss) for x, y in poly], fill=255)
        S = np.asarray(S) > 127
        din = cv2.distanceTransform(S.astype(np.uint8), cv2.DIST_L2, 5) / ss
        tw = L.get('tw', 4.0)
        band = S & (din <= tw)
        t = cv2.resize(band.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA) > 0.45
        for gx, gy, gr in L.get('gaps') or []:
            yy, xx = np.ogrid[0:H, 0:W]
            t &= (xx - gx) ** 2 + (yy - gy) ** 2 > gr * gr
        newtube |= t
    # стёртое место: свечение оставшихся букв (по той же таблице), сверху — новая буква
    rest = lut.render(core & ~old_all)
    pm[erase_all] = rest[erase_all]
    new = lut.render(newtube)
    out = np.maximum(pm, new)
    return Image.fromarray(lutfx.unpremul(out))
