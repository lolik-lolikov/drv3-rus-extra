"""Показать пары оригинал|текущий перевод|новый (build) для текстур по имени. python3 audit/view.py OUT.png [scale] name1 name2 ...
имя: подстрока texname или file:texname"""
import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
res = json.load(open(os.path.join(ROOT, 'audit/scan.json')))
out = sys.argv[1]; scale = float(sys.argv[2]); names = sys.argv[3:]
F = ImageFont.truetype(os.path.join(ROOT, 'work/fonts/rubik_400.ttf'), 14)
from drv3 import spc_read
from srdtex import textures, decode
def build_img(r):
    # найти собранный файл в build/
    rel = r[0]
    cands = glob.glob(os.path.join(ROOT, 'build/**/' + os.path.basename(rel)), recursive=True)
    cands = [c for c in cands if c.replace(os.sep, '/').endswith(rel.split('/', 1)[1] if rel.startswith('flash/rsc/') else rel)] or cands
    for c in cands:
        spc = spc_read(open(c, 'rb').read())
        tgt = spc
        for part in [p for p in r[1].split('/') if p]:
            tgt = spc_read([e for e in tgt['entries'] if e.name == part][0].data)
        E = {e.name: e for e in tgt['entries']}
        if r[2] in E and r[2] + 'v' in E:
            for t in textures(E[r[2]].data):
                if t['name'] == r[3]:
                    return decode(t, E[r[2] + 'v'].data)
    return None
def checker(w, h):
    im = Image.new('RGBA', (w, h), (80, 80, 90, 255)); d = ImageDraw.Draw(im)
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            if (x // 16 + y // 16) % 2: d.rectangle((x, y, x + 15, y + 15), fill=(110, 110, 120, 255))
    return im
rows = []; seen = set()
for nm in names:
    for r in res:
        key = r[0] + ':' + r[3]
        if (nm in r[3] if ':' not in nm else nm in key) and r[8]:
            k2 = (r[3], open(r[8], 'rb').read()[:2000])
            if k2 in seen: continue
            seen.add(k2)
            ims = [Image.open(r[8]).convert('RGBA')]
            if r[9]: ims.append(Image.open(r[9]).convert('RGBA'))
            if os.environ.get('BUILD'):
                b = build_img(r)
                if b is not None: ims.append(b)
            rows.append((r[0].split('/')[-1] + ':' + r[3], ims))
W = 0; H = 0
for lab, ims in rows:
    w = sum(int(i.width * scale) + 10 for i in ims); W = max(W, w); H += int(ims[0].height * scale) + 20
C = Image.new('RGBA', (max(W, 300), H), (30, 30, 36, 255)); d = ImageDraw.Draw(C); y = 0
for lab, ims in rows:
    d.text((2, y), lab, font=F, fill=(255, 230, 80, 255)); y += 18; x = 0
    for i in ims:
        i2 = i.resize((int(i.width * scale), int(i.height * scale)), Image.LANCZOS if scale < 1 else Image.NEAREST)
        C.alpha_composite(checker(*i2.size), (x, y)); C.alpha_composite(i2, (x, y)); x += i2.width + 10
    y += int(ims[0].height * scale) + 2
C.convert('RGB').save(out); print(len(rows), C.size)
