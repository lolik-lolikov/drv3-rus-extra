"""Сравнение «оригинал | v2.3 (cur/) | v2.4 (build/)» для всех текстур из описаний.
python3 audit/compare_build.py <папка_вывода> [--all]
Без --all — только текстуры, которые в v2.4 отличаются от v2.3. Листы по ~14 строк, plus список изменений list.txt."""
import os, sys, glob
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
os.chdir(ROOT)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import texedit
from tex_specs import SPECS
from drv3 import spc_read
from srdtex import textures, decode

OUT = sys.argv[1]; ALL = '--all' in sys.argv
os.makedirs(OUT, exist_ok=True)
specs = texedit.expand_specs(SPECS)
srcs = {os.path.basename(p).lower(): p for p in glob.glob('cur/**/*', recursive=True) if os.path.isfile(p)}
cache = {}


def tex_of(path, inner, srd, tex):
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


rows = []; seen = set()
for s in specs:
    key = (os.path.basename(s['arch']), s.get('inner'), s.get('srd'), s['tex'])
    if key in seen:
        continue
    seen.add(key)
    op = os.path.join('orig', s['arch']); bp = texedit.out_path(s['arch'])
    cp = srcs.get(os.path.basename(s['arch']).lower())
    o = tex_of(op, s.get('inner'), s.get('srd'), s['tex'])
    n = tex_of(bp, s.get('inner'), s.get('srd'), s['tex']) if os.path.exists(bp) else None
    c = tex_of(cp, s.get('inner'), s.get('srd'), s['tex']) if cp else None
    if o is None or n is None:
        continue
    same = c is not None and c.size == n.size and np.abs(np.asarray(c).astype(int) - np.asarray(n).astype(int)).max() <= 8
    if same and not ALL:
        continue
    rows.append((os.path.basename(s['arch']) + ':' + s['tex'], o, c, n, 'новая' if c is None or np.array_equal(np.asarray(c), np.asarray(o)) else 'изменена'))

F = ImageFont.truetype('work/fonts/rubik_400.ttf', 15)


def checker(w, h):
    im = Image.new('RGBA', (w, h), (64, 64, 74, 255)); d = ImageDraw.Draw(im)
    for y in range(0, h, 12):
        for x in range(0, w, 12):
            if (x // 12 + y // 12) % 2: d.rectangle((x, y, x + 11, y + 11), fill=(86, 86, 98, 255))
    return im


with open(os.path.join(OUT, 'list.txt'), 'w', encoding='utf-8') as fh:
    for r in rows:
        fh.write('%s\t%s\n' % (r[4], r[0]))
per = 12; k = 0
for i in range(0, len(rows), per):
    part = rows[i:i + per]
    prep = []
    for lab, o, c, n, kind in part:
        f = min(1.0, 440 / o.width, 150 / o.height)
        sz = (max(1, int(o.width * f)), max(1, int(o.height * f)))
        ims = [o.resize(sz, Image.LANCZOS), (c.resize(sz, Image.LANCZOS) if c is not None else None), n.resize(sz, Image.LANCZOS)]
        prep.append((lab + '  [' + kind + ']', ims))
    W = 3 * 450 + 20; H = sum(p[1][0].height + 26 for p in prep) + 24
    C = Image.new('RGBA', (W, H), (28, 28, 34, 255)); d = ImageDraw.Draw(C)
    d.text((4, 2), 'оригинал', font=F, fill=(200, 200, 200, 255)); d.text((464, 2), 'v2.3', font=F, fill=(200, 200, 200, 255))
    d.text((924, 2), 'v2.4', font=F, fill=(120, 255, 140, 255))
    y = 24
    for lab, ims in prep:
        d.text((4, y), lab, font=F, fill=(255, 220, 90, 255)); y += 20
        for j, im in enumerate(ims):
            if im is None: continue
            ch = checker(*im.size); ch.alpha_composite(im); C.paste(ch, (4 + j * 460, y))
        y += ims[0].height + 6
    k += 1
    C.convert('RGB').save(os.path.join(OUT, 'sheet_%02d.png' % k))
print(len(rows), 'текстур,', k, 'листов ->', OUT)
