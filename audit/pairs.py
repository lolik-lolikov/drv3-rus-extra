"""Листы пар оригинал|перевод для изменённых текстур (без дублей). python3 audit/pairs.py OUTPREFIX [filters...]"""
import os, sys, json, hashlib
from PIL import Image, ImageDraw, ImageFont
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), '..')
res = json.load(open(os.path.join(ROOT, 'audit/scan.json')))
out = sys.argv[1]; flt = sys.argv[2:]
EX = [x for x in os.environ.get('EXCL', '').split(',') if x]
F = ImageFont.truetype(os.path.join(ROOT, 'work/fonts/rubik_400.ttf'), 13)
MW, MH = int(os.environ.get('MW', 520)), int(os.environ.get('MH', 220))
seen = set(); items = []
for r in res:
    if r[7] is not True or not r[9]: continue
    if flt and not any(f in r[0] + '|' + r[1] + '|' + r[3] for f in flt): continue
    if any(x in r[0] + '|' + r[3] for x in EX): continue
    h = hashlib.md5(open(r[9], 'rb').read()).hexdigest()
    if h in seen: continue
    seen.add(h); items.append(r)
def checker(w, h, c1=(70, 70, 80), c2=(100, 100, 110)):
    im = Image.new('RGBA', (w, h), c1 + (255,)); d = ImageDraw.Draw(im)
    for y in range(0, h, 10):
        for x in range(0, w, 10):
            if (x // 10 + y // 10) % 2: d.rectangle((x, y, x + 9, y + 9), fill=c2 + (255,))
    return im
W = 1500; page = 0; C = None; x = y = rowh = 0
lst = open(out + '_list.txt', 'w')
for i, r in enumerate(items):
    a = Image.open(r[8]).convert('RGBA'); b = Image.open(r[9]).convert('RGBA')
    k = min(1.0, MW / a.width, MH / a.height)
    sz = (max(1, int(a.width * k)), max(1, int(a.height * k)))
    a = a.resize(sz, Image.LANCZOS); b = b.resize(sz, Image.LANCZOS)
    cw = max(2 * sz[0] + 6, 260); ch = sz[1] + 16
    if C is None: C = Image.new('RGBA', (W, 1700), (30, 30, 36, 255)); x = y = rowh = 0
    if x + cw > W: x = 0; y += rowh + 8; rowh = 0
    if y + ch > 1700:
        C.convert('RGB').save('%s_%02d.png' % (out, page)); page += 1
        C = Image.new('RGBA', (W, 1700), (30, 30, 36, 255)); x = y = rowh = 0
    d = ImageDraw.Draw(C)
    lab = '#%d %s:%s %dx%d' % (i, os.path.basename(r[0]).replace('_US', '').replace('.spc', '').replace('.SPC', ''), (r[1].split('/')[-1] + ':' if r[1] else '') + r[3].replace('.png', ''), r[4], r[5])
    d.text((x + 2, y), lab[:int(cw / 6.3)], font=F, fill=(255, 230, 80, 255))
    C.alpha_composite(checker(*sz), (x, y + 16)); C.alpha_composite(a, (x, y + 16))
    C.alpha_composite(checker(*sz), (x + sz[0] + 6, y + 16)); C.alpha_composite(b, (x + sz[0] + 6, y + 16))
    lst.write('#%d\t%s\t%s\t%s\t%s\n' % (i, r[0], r[1], r[3], r[9]))
    x += cw + 10; rowh = max(rowh, ch)
if C is not None: C.convert('RGB').save('%s_%02d.png' % (out, page)); page += 1
print(len(items), 'items', page, 'pages')
