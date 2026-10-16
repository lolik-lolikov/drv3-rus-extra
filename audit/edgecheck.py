"""Проверка собранных текстур (build/): надпись не должна выходить за поля, которые были у оригинала
(как texedit.allowed_box), и не должна быть пустой. python3 audit/edgecheck.py [подстрока имени]
Печатает список подозрительных текстур и сохраняет audit/edge_<n>.png (оригинал | собранная)."""
import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
os.chdir(ROOT)
import numpy as np
from PIL import Image, ImageDraw
import texedit
from tex_specs import SPECS
from drv3 import spc_read
from srdtex import textures, decode

flt = sys.argv[1] if len(sys.argv) > 1 else ''
specs = [s for s in texedit.expand_specs(SPECS) if flt in s['tex'] or flt in s['arch']]
cache = {}


def arch_tex(path, inner, srd, tex):
    key = (path, inner)
    if key not in cache:
        spc = spc_read(open(path, 'rb').read())
        if inner:
            spc = spc_read([e for e in spc['entries'] if e.name == inner][0].data)
        cache[key] = {e.name: e for e in spc['entries']}
    E = cache[key]
    for n in E:
        if n.endswith('.srd') and n + 'v' in E and (not srd or srd == n):
            for t in textures(E[n].data):
                if t['name'] == tex:
                    return decode(t, E[n + 'v'].data)


bad = []
for s in specs:
    op = os.path.join(ROOT, 'orig', s['arch']); bp = texedit.out_path(s['arch'])
    if not os.path.exists(bp):
        bad.append((s, 'НЕТ СБОРКИ')); continue
    o = arch_tex(op, s.get('inner'), s.get('srd'), s['tex']); n = arch_tex(bp, s.get('inner'), s.get('srd'), s['tex'])
    if o is None or n is None:
        bad.append((s, 'НЕТ ТЕКСТУРЫ')); continue
    if np.array_equal(np.asarray(o), np.asarray(n)):
        bad.append((s, 'НЕ ИЗМЕНЕНА')); continue
    if s.get('custom') is not None and s.get('fit') is None and not s.get('edge_check'):
        continue          # особые надписи (пиксель-арт, неон, буквы по одной) проверяются глазами
    ab = texedit.allowed_box(o, dict(s))
    a = np.asarray(n)[:, :, 3]
    if a.min() > 200:      # непрозрачные (DXT1) — не проверяем
        continue
    ys, xs = np.where(a > 40)
    if not len(xs):
        bad.append((s, 'ПУСТАЯ')); continue
    if not (xs.min() >= ab[0] and ys.min() >= ab[1] and xs.max() < ab[2] and ys.max() < ab[3]):
        side = ''.join(c for c, f in zip('LTRB', (xs.min() < ab[0], ys.min() < ab[1], xs.max() >= ab[2], ys.max() >= ab[3])) if f)
        bad.append((s, 'КРАЙ ' + side, o, n))
print(len(specs), 'проверено;', len(bad), 'замечаний')
rows = []
for b in bad:
    s, why = b[0], b[1]
    print('%-14s %s : %s' % (why, s['arch'].split('/')[-1], s['tex']))
    if len(b) > 2:
        rows.append((s['arch'].split('/')[-1] + ':' + s['tex'] + '  ' + why, b[2], b[3]))
if rows:
    def checker(w, h):
        im = Image.new('RGBA', (w, h), (80, 80, 90, 255)); d = ImageDraw.Draw(im)
        for y in range(0, h, 16):
            for x in range(0, w, 16):
                if (x // 16 + y // 16) % 2: d.rectangle((x, y, x + 15, y + 15), fill=(110, 110, 120, 255))
        return im
    prep = []
    for lab, o, n in rows:
        f = min(1.0, 600 / o.width, 200 / o.height)
        sz = (max(1, int(o.width * f)), max(1, int(o.height * f)))
        prep.append((lab, o.resize(sz, Image.LANCZOS), n.resize(sz, Image.LANCZOS)))
    W = max(p[1].width * 2 + 30 for p in prep); H = sum(p[1].height + 20 for p in prep)
    C = Image.new('RGBA', (W, H), (30, 30, 36, 255)); d = ImageDraw.Draw(C); y = 0
    for lab, o, n in prep:
        d.text((2, y), lab, fill=(255, 120, 120, 255)); y += 14
        c1 = checker(*o.size); c1.alpha_composite(o); C.paste(c1, (0, y))
        c2 = checker(*n.size); c2.alpha_composite(n); C.paste(c2, (o.width + 20, y)); y += o.height + 6
    C.save('audit/edge_report.png'); print('audit/edge_report.png', C.size)
